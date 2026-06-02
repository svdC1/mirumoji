/**
 * @packageDocumentation This component is the transcribe page of the application.
 * It allows the user to record or upload audio and have it transcribed.
 */

import { useRef, useState, useLayoutEffect, ChangeEvent } from "react";
import { toast } from "react-hot-toast";
import { uploadFile } from "@/shared/api/client";
import { apiTokenize } from "@/shared/dict/api";
import { apiExplainSentence, apiGetTemplate } from "@/shared/llm/api";
import { ApiError } from "@/shared/api/errors";
import AudioPlayer from "react-h5-audio-player";
import "react-h5-audio-player/lib/styles.css";
import WordDialog from "@/shared/components/WordDialog";
import type { Message, AudioTranscriptResponse } from "@/features/transcribe/types";
import ChatBubble from "../components/ChatBubble";
/**
 * The TranscribePage component.
 *
 * This component is responsible for the following:
 * - Recording audio.
 * - Uploading audio.
 * - Transcribing audio.
 * - Displaying the transcription.
 * - Displaying a GPT-powered explanation of the transcription.
 *
 * @returns {JSX.Element} The TranscribePage component.
 */
export default function TranscribePage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [cleanAudio, setCleanAudio] = useState(false);
    const [llmExplain, setLlmExplain] = useState(false);
    const [recording, setRecording] = useState(false);
    const [recordedFile, setRecordedFile] = useState<File | null>(null);
    const [uploadedFile, setUploadedFile] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string>("");
    const [sending, setSending] = useState(false);
    const [dialog, setDialog] = useState<{
        sentence: string;
        word: string;
    } | null>(null);

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const mediaStreamRef = useRef<MediaStream | null>(null);
    const chunksRef = useRef<BlobPart[]>([]);
    const chatEndRef = useRef<HTMLDivElement | null>(null);
    const fileInputRef = useRef<HTMLInputElement | null>(null);

    useLayoutEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const getSupportedMimeType = () => {
        const types = [
            "audio/webm;codecs=opus",
            "audio/mp4",
            "audio/wav",
            "audio/aac",
            "audio/webm",
        ];
        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }
        return null;
    };

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true,
            });
            mediaStreamRef.current = stream;
            const mimeType = getSupportedMimeType();
            if (!mimeType) {
                toast.error("No supported audio MIME type found.");
                stream.getTracks().forEach((track) => track.stop());
                return;
            }
            const recorder = new MediaRecorder(stream, { mimeType });
            mediaRecorderRef.current = recorder;
            chunksRef.current = [];
            recorder.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
            };
            recorder.onstop = () => {
                const blob = new Blob(chunksRef.current, { type: mimeType });
                let fileExtension = mimeType.split(/[/;]+/)[1] || "ogg";
                if (fileExtension === "opus") fileExtension = "webm";
                if (fileExtension === "mp4") fileExtension = "mp4";
                if (fileExtension === "wav") fileExtension = "wav";
                if (fileExtension === "aac") fileExtension = "aac";
                const file = new File([blob], `recording.${fileExtension}`, {
                    type: mimeType,
                });
                setRecordedFile(file);
                setPreviewUrl(URL.createObjectURL(file));
                if (mediaStreamRef.current) {
                    mediaStreamRef.current.getTracks().forEach((track) => track.stop());
                    mediaStreamRef.current = null;
                }
            };
            recorder.start();
            setRecording(true);
            setUploadedFile(null);
            setPreviewUrl("");
        } catch (error) {
            console.error("Error starting recording:", error);
            toast.error("Unable to access microphone.");
            if (mediaStreamRef.current) {
                mediaStreamRef.current.getTracks().forEach((track) => track.stop());
                mediaStreamRef.current = null;
            }
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current) {
            mediaRecorderRef.current.stop();
            setRecording(false);
        }
    };

    const deleteMedia = () => {
        setRecordedFile(null);
        setUploadedFile(null);
        setPreviewUrl("");
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
        if (mediaStreamRef.current) {
            mediaStreamRef.current.getTracks().forEach((track) => track.stop());
            mediaStreamRef.current = null;
        }
    };

    const handleFileUpload = (event: ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            setUploadedFile(file);
            setRecordedFile(null);
            setPreviewUrl(URL.createObjectURL(file));
        }
    };

    const sendAudio = async () => {
        const fileToSend = recordedFile || uploadedFile;
        if (!fileToSend) return;

        setSending(true);
        const tId = toast.loading("Uploading...");
        const loaderId = `loader-${Date.now()}`;
        const userMessageId = `user-${Date.now() + 1}`;

        setMessages((prev) => [
            ...prev,
            {
                id: userMessageId,
                type: "user",
                audioUrl: previewUrl,
                isAudioMessage: true,
            },
            { id: loaderId, type: "bot", loading: true, isAudioMessage: true },
        ]);

        try {
            const query = `clean_audio=${cleanAudio}&language=ja`;
            const result = await uploadFile<AudioTranscriptResponse>(
                fileToSend,
                `audio/transcribe?${query}`,
                {},
                (progress: number) => {
                    toast.loading(`Uploading... ${progress.toFixed(0)}%`, {
                        id: tId,
                    });
                },
                () => {
                    toast.dismiss(tId);
                }
            );

            const newMessages: Message[] = [];

            if (result.transcript) {
                // Tokenize the transcript on the server for clickable furigana
                let words;
                try {
                    words = await apiTokenize(result.transcript);
                } catch (e) {
                    console.error("Failed to tokenize transcript:", e);
                }
                newMessages.push({
                    id: `text-${Date.now() + 2}`,
                    type: "bot",
                    text: result.transcript,
                    words,
                    isTranscription: true,
                });
            }

            // Optional sentence explanation (separate LLM call, model from the
            // profile template)
            if (llmExplain && result.transcript) {
                const template = await apiGetTemplate();
                if (!template) {
                    toast.error("Configure an LLM model in your Profile to enable explanations.");
                } else {
                    const { explanation } = await apiExplainSentence({
                        sentence: result.transcript,
                        model: template.model,
                        sys_msg: template.sys_msg || undefined,
                    });
                    newMessages.push({
                        id: `explain-${Date.now() + 3}`,
                        type: "bot",
                        text: explanation,
                    });
                }
            }

            setMessages((prev) => [...prev.filter((m) => m.id !== loaderId), ...newMessages]);
            deleteMedia();
        } catch (err: any) {
            let errorMessage = "An unknown error occurred during transcription.";
            if (err instanceof ApiError) {
                errorMessage = `Error ${err.status}: ${err.message}`;
            } else if (err instanceof Error) {
                errorMessage = err.message;
            }
            setMessages((prev) => [
                ...prev.filter((m) => m.id !== loaderId),
                {
                    id: `err-${Date.now()}`,
                    type: "bot",
                    text: errorMessage,
                },
            ]);
        } finally {
            setSending(false);
        }
    };

    const clearChat = () => {
        setMessages([]);
        deleteMedia();
    };

    const handleWordClick = (sentence: string, word: string) => {
        setDialog({ sentence, word });
    };

    return (
        <div className="flex flex-col h-screen bg-black text-white">
            <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
                {messages.map((msg) => (
                    <ChatBubble key={msg.id} msg={msg} onWordClick={handleWordClick} />
                ))}
                <div ref={chatEndRef} />
            </div>

            {dialog && (
                <WordDialog
                    sentence={dialog.sentence}
                    word={dialog.word}
                    cueEnd={0}
                    cueStart={0}
                    videoFile={null}
                    onClose={() => setDialog(null)}
                />
            )}

            <div className="p-4 border-t select-none border-zinc-700 space-y-4">
                {previewUrl && (
                    <AudioPlayer
                        src={previewUrl}
                        layout="horizontal"
                        showJumpControls={false}
                        customAdditionalControls={[]}
                        className="rounded-md"
                    />
                )}

                <div className="flex gap-2 text-sm">
                    <button
                        onClick={() => setCleanAudio((prev) => !prev)}
                        className={`flex-1 py-2 rounded-full font-semibold transition-all ${
                            cleanAudio ? "bg-indigo-600" : "bg-zinc-700"
                        }`}
                    >
                        Clean Audio
                    </button>
                    <button
                        onClick={() => setLlmExplain((prev) => !prev)}
                        className={`flex-1 py-2 rounded-full font-semibold transition-all ${
                            llmExplain ? "bg-indigo-600" : "bg-zinc-700"
                        }`}
                    >
                        LLM Explain
                    </button>
                    <button
                        onClick={clearChat}
                        className="flex-1 py-2 rounded-full font-semibold transition-all bg-red-600 hover:bg-red-500"
                    >
                        Clear Chat
                    </button>
                </div>

                {previewUrl ? (
                    <div className="flex gap-2">
                        <button
                            onClick={deleteMedia}
                            disabled={sending}
                            className="flex-1 py-2 rounded-lg bg-red-600 text-white hover:bg-red-500 disabled:opacity-50"
                        >
                            Delete
                        </button>
                        <button
                            onClick={sendAudio}
                            disabled={sending}
                            className="flex-1 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-50"
                        >
                            {sending ? "Sending…" : "Send Audio"}
                        </button>
                    </div>
                ) : (
                    <div className="flex gap-2">
                        <button
                            onClick={recording ? stopRecording : startRecording}
                            disabled={sending}
                            className={`flex-1 py-2 rounded-lg text-white disabled:opacity-50 ${
                                recording
                                    ? "bg-red-600 hover:bg-red-500"
                                    : "bg-green-600 hover:bg-green-500"
                            }`}
                        >
                            {recording ? "Stop Recording" : "Start Recording"}
                        </button>
                        <label
                            htmlFor="file-upload"
                            className={`flex-1 py-2 rounded-lg text-white text-center cursor-pointer ${
                                sending
                                    ? "bg-zinc-700 opacity-50 cursor-not-allowed"
                                    : "bg-blue-600 hover:bg-blue-500"
                            }`}
                        >
                            Upload Audio
                        </label>
                        <input
                            id="file-upload"
                            type="file"
                            accept="audio/*"
                            ref={fileInputRef}
                            onChange={handleFileUpload}
                            className="hidden"
                            disabled={sending}
                        />
                    </div>
                )}
            </div>
        </div>
    );
}
