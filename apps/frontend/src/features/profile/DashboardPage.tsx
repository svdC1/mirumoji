/**
 * @packageDocumentation The Dashboard — the single user-data hub. Tabs for
 * Profile, Files, Transcripts, Clips, and the LLM Template.
 */

import { useState } from "react";
import { Tabs } from "@/shared/ui";
import { tabs } from "./constants";
import { ProfilePanel } from "./components/ProfilePanel";
import { FilesPanel } from "./components/FilesPanel";
import { TranscriptsPanel } from "./components/TranscriptsPanel";
import { ClipsPanel } from "./components/ClipsPanel";
import { LlmTemplatePanel } from "./components/LlmTemplatePanel";

/**
 * The DashboardPage component.
 *
 * @returns {JSX.Element} The dashboard.
 */
export default function DashboardPage() {
    const [tab, setTab] = useState("profile");

    return (
        <div className="mx-auto min-h-[calc(100dvh_-_3.5rem)] md:min-h-dvh w-full max-w-4xl px-4 py-8">
            <h1 className="mb-6 font-display text-3xl text-ink">Dashboard</h1>
            <Tabs items={tabs} value={tab} onChange={setTab} className="mb-6" />

            {tab === "profile" && <ProfilePanel />}
            {tab === "files" && <FilesPanel />}
            {tab === "transcripts" && <TranscriptsPanel />}
            {tab === "clips" && <ClipsPanel />}
            {tab === "llm-template" && <LlmTemplatePanel />}
        </div>
    );
}
