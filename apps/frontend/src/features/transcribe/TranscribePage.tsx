/**
 * @packageDocumentation The Transcribe page: record or upload audio, transcribe
 * it (clickable furigana), and optionally get an LLM sentence explanation.
 */

import { useRef, useState, useLayoutEffect, ChangeEvent } from "react";
import { toast } from "react-hot-toast";
import { Mic, Square, Upload, Trash2, Send } from "lucide-react";
import { apiTokenize } from "@/shared/dict/api";
import { useBundleSettings } from "@/contexts/BundleSettingsContext";
import { useTasks } from "@/contexts/TaskContext";
import { apiGetTemplate, streamExplain } from "@/shared/llm/api";
import { toastApiError } from "@/shared/api/errors";
import WordDialog from "@/shared/components/WordDialog";
import { AudioPlayer, Button, buttonClasses, cn } from "@/shared/ui";
import type { Message } from "./types";
import type { TranscribeResult } from "@/shared/jobs/types";
import ChatBubble from "./components/ChatBubble";

/**
 * The TranscribePage component.
 *
 * @returns {JSX.Element} The transcribe page.
 */
export default function TranscribePage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [cleanAudio, setCleanAudio] = useState(false);
    const [llmExplain, setLlmExplain] = useState(false);
    const [recording, setRecording] = useState(false);
    const [recordedFile, setRecordedFile] = useState<File | null>(null);
    const [uploadedFile, setUploadedFile] = useState<File | null>(null);
    const [previewUrl, setPreviewUrl] = useState("");
    const [sending, setSending] = useState(false);
    const [dialog, setDialog] = useState<{ sentence: string; word: string } | null>(null);
    const { mode } = useBundleSettings();
    const tasks = useTasks();

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
        return types.find((t) => MediaRecorder.isTypeSupported(t)) ?? null;
    };

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaStreamRef.current = stream;
            const mimeType = getSupportedMimeType();
            if (!mimeType) {
                toast.error("No Supported Audio Format Found");
                stream.getTracks().forEach((t) => t.stop());
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
                let ext = mimeType.split(/[/;]+/)[1] || "ogg";
                if (ext === "opus") ext = "webm";
                const file = new File([blob], `recording.${ext}`, { type: mimeType });
                setRecordedFile(file);
                setPreviewUrl(URL.createObjectURL(file));
                if (mediaStreamRef.current) {
                    mediaStreamRef.current.getTracks().forEach((t) => t.stop());
                    mediaStreamRef.current = null;
                }
            };
            recorder.start();
            setRecording(true);
            setUploadedFile(null);
            setPreviewUrl("");
        } catch (error) {
            console.error("Error starting recording:", error);
            toast.error("Unable To Access Microphone");
            if (mediaStreamRef.current) {
                mediaStreamRef.current.getTracks().forEach((t) => t.stop());
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
        if (fileInputRef.current) fileInputRef.current.value = "";
        if (mediaStreamRef.current) {
            mediaStreamRef.current.getTracks().forEach((t) => t.stop());
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
        const loaderId = `loader-${Date.now()}`;
        const userMessageId = `user-${Date.now() + 1}`;

        setMessages((prev) => [
            ...prev,
            { id: userMessageId, type: "user", audioUrl: previewUrl, isAudioMessage: true },
            { id: loaderId, type: "bot", loading: true, isAudioMessage: true },
        ]);
        const dropLoader = () => setMessages((prev) => prev.filter((m) => m.id !== loaderId));

        try {
            // Submit a transcribe job (tracked in the tray) and wait for it
            // inline so the transcript still lands in the chat.
            const job = await tasks.uploadAndSubmit(fileToSend, {
                jobType: "transcribe",
                fileType: "audio",
                opts: { clean_audio: cleanAudio, language: "ja" },
            });
            if (!job) {
                // Upload / submit failed (the tray surfaces it).
                dropLoader();
                return;
            }
            const done = await tasks.waitFor(job.id);
            if (done.status !== "succeeded" || !done.result) {
                // Failed / cancelled (the tray + a toast surface it).
                dropLoader();
                return;
            }

            const { transcript } = done.result as unknown as TranscribeResult;
            let words: Awaited<ReturnType<typeof apiTokenize>> | undefined;
            try {
                words = await apiTokenize(transcript, mode);
            } catch (e) {
                console.error("Failed to tokenize transcript:", e);
            }
            dropLoader();
            setMessages((prev) => [
                ...prev,
                {
                    id: `text-${Date.now()}`,
                    type: "bot",
                    text: transcript,
                    words,
                    isTranscription: true,
                },
            ]);
            deleteMedia();

            if (llmExplain) {
                const template = await apiGetTemplate();
                if (!template) {
                    toast.error("Configure An LLM Model In Your Profile To Enable Explanations");
                    return;
                }
                // Stream the explanation into its own bubble as it arrives.
                const explainId = `explain-${Date.now()}`;
                setMessages((prev) => [...prev, { id: explainId, type: "bot", text: "" }]);
                try {
                    await streamExplain(
                        {
                            sentence: transcript,
                            model: template.model,
                            sys_msg: template.sys_msg || undefined,
                        },
                        {
                            onToken: (t) =>
                                setMessages((prev) =>
                                    prev.map((m) =>
                                        m.id === explainId ? { ...m, text: (m.text ?? "") + t } : m
                                    )
                                ),
                        }
                    );
                } catch (err) {
                    toastApiError(err);
                }
            }
        } catch (err) {
            toastApiError(err);
            dropLoader();
        } finally {
            setSending(false);
        }
    };

    const clearChat = () => {
        setMessages([]);
        deleteMedia();
    };

    const toggleClass = (active: boolean) =>
        cn(
            "flex-1 rounded-control py-2 text-sm font-medium transition-colors",
            active ? "bg-shu/15 text-shu" : "bg-surface-2 text-ink-muted hover:text-ink"
        );

    return (
        <div className="flex h-[calc(100dvh_-_3.5rem)] flex-col bg-bg text-ink md:h-dvh">
            <div className="flex-1 overflow-y-auto">
                <div className="mx-auto max-w-3xl space-y-4 px-4 py-6">
                    {messages.length === 0 ? (
                        <p className="pt-20 text-center text-sm text-ink-faint">
                            Record Or Upload Audio To Get A Clickable Transcript
                        </p>
                    ) : (
                        messages.map((msg) => (
                            <ChatBubble
                                key={msg.id}
                                msg={msg}
                                onWordClick={(s, w) => setDialog({ sentence: s, word: w })}
                            />
                        ))
                    )}
                    <div ref={chatEndRef} />
                </div>
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

            <div className="select-none border-t border-ink/10 bg-surface/60 backdrop-blur">
                <div className="mx-auto max-w-3xl space-y-3 p-4">
                    {previewUrl && <AudioPlayer src={previewUrl} />}

                    <div className="flex gap-2">
                        <button
                            onClick={() => setCleanAudio((v) => !v)}
                            className={toggleClass(cleanAudio)}
                        >
                            Clean
                        </button>
                        <button
                            onClick={() => setLlmExplain((v) => !v)}
                            className={toggleClass(llmExplain)}
                        >
                            LLM
                        </button>
                        <Button variant="ghost" className="flex-1" onClick={clearChat}>
                            Clear
                        </Button>
                    </div>

                    {previewUrl ? (
                        <div className="flex gap-2">
                            <Button
                                variant="danger"
                                className="flex-1"
                                onClick={deleteMedia}
                                disabled={sending}
                            >
                                <Trash2 size={16} /> Delete
                            </Button>
                            <Button className="flex-1" onClick={sendAudio} loading={sending}>
                                <Send size={16} /> Send
                            </Button>
                        </div>
                    ) : (
                        <div className="flex gap-2">
                            <Button
                                variant={recording ? "danger" : "primary"}
                                className="flex-1"
                                onClick={recording ? stopRecording : startRecording}
                                disabled={sending}
                            >
                                {recording ? <Square size={16} /> : <Mic size={16} />}
                                {recording ? "Stop" : "Start"}
                            </Button>
                            <label
                                htmlFor="file-upload"
                                className={buttonClasses(
                                    "secondary",
                                    "md",
                                    cn(
                                        "flex-1 cursor-pointer",
                                        sending && "pointer-events-none opacity-50"
                                    )
                                )}
                            >
                                <Upload size={16} /> Upload
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
        </div>
    );
}
