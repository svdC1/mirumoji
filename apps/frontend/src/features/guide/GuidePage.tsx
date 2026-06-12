/**
 * @packageDocumentation The Guide page — concise how-tos for the main flows.
 */

import {
    User,
    Clapperboard,
    FileText,
    List,
    Bookmark,
    Sparkles,
    Mic,
    Languages,
} from "lucide-react";
import { Card } from "@/shared/ui";

interface Step {
    icon: typeof User;
    title: string;
    body: string;
}

const STEPS: Step[] = [
    {
        icon: User,
        title: "Set A Profile",
        body: "Open the profile chip at the bottom of the sidebar (or the Dashboard) and pick a name. Your files, clips, transcripts, and LLM template will be saved on the server and linked to the active profile at creation time",
    },
    {
        icon: Clapperboard,
        title: "Load A Video",
        body: "On the Player, use Load to open a video + subtitle files from your device or your profile. Non-MP4 files can be converted in the toolbar for player compatibility",
    },
    {
        icon: FileText,
        title: "Generate Or Fix Subtitles",
        body: "Generate subtitles in SRT format from the video's audio and prompt an LLM to fix transcription errors through the player's toolbar",
    },
    {
        icon: List,
        title: "Navigate Subtitles",
        body: "The subtitle side panel in the player page lists every cue. Search for specific words or click a cue to skip the video to its timestamp. The active line auto-scrolls into view as you watch the video. You can also click any word in the rendered subtitles for a dictionary lookup",
    },
    {
        icon: Bookmark,
        title: "Save Clips & Export Anki",
        body: "From a word lookup pop-up, click the bookmark icon to save a clip to your profile. Collect clips in the Dashboard's Clips tab and export them all as an Anki deck",
    },
    {
        icon: Sparkles,
        title: "Configure An LLM",
        body: "In the Dashboard's LLM Template tab, choose one of the backend's configured providers, write the name of a model, and tune the system and prompt messages used for word breakdowns and explanations",
    },
    {
        icon: Mic,
        title: "Transcribe Audio",
        body: "Record or upload audio to get a clickable transcript. The Clean Audio checkbox allows you to apply a band-pass + loudness normalisation on the raw audio before transcription to get the best results. The LLM Explanation checkbox allows you to prompt the configured LLM for an explanation of the transcription",
    },
    {
        icon: Languages,
        title: "Analyze Text",
        body: "Paste any Japanese into the Text Analyzer to read it with furigana and tap words for lookups",
    },
];

/**
 * The GuidePage component.
 *
 * @returns {JSX.Element} The guide page.
 */
export default function GuidePage() {
    return (
        <div className="mx-auto min-h-screen w-full max-w-3xl px-4 py-10">
            <h1 className="mb-2 font-display text-3xl text-ink">Guide</h1>
            <p className="mb-8 text-ink-muted">How To Use Mirumoji</p>

            <div className="space-y-3">
                {STEPS.map(({ icon: Icon, title, body }) => (
                    <Card key={title} className="flex gap-4 p-5">
                        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-shu/15 text-shu">
                            <Icon size={20} />
                        </span>
                        <div>
                            <h2 className="font-display text-lg text-ink">{title}</h2>
                            <p className="mt-1 text-sm leading-relaxed text-ink-muted">{body}</p>
                        </div>
                    </Card>
                ))}
            </div>
        </div>
    );
}
