/**
 * @packageDocumentation The Dashboard — the single user-data hub. Tabs for
 * Profile, Files, Transcripts, Clips, and the LLM Template.
 */

import { useState } from "react";
import { Tabs } from "@/shared/ui";
import { tabs } from "./constants";
import { ProfilePanel } from "@/features/profile/components/ProfilePanel";
import { FilesPanel } from "@/features/profile/components/FilesPanel";
import { TranscriptsPanel } from "@/features/profile/components/TranscriptsPanel";
import { ClipsPanel } from "@/features/profile/components/ClipsPanel";
import { TasksPanel } from "@/features/profile/components/TasksPanel";
import { LlmTemplatePanel } from "@/features/profile/components/LlmTemplatePanel";
import { AdvancedPanel } from "@/features/profile/components/AdvancedPanel";

/**
 * The DashboardPage component.
 *
 * @returns {JSX.Element} The dashboard.
 */
export default function DashboardPage() {
    const [tab, setTab] = useState("profile");

    return (
        <div className="mx-auto min-h-[var(--content-h)] lg:min-h-dvh w-full max-w-4xl px-[calc(1rem_+_var(--safe-x))] py-8">
            <h1 className="mb-6 font-display text-3xl text-ink">Dashboard</h1>
            <Tabs items={tabs} value={tab} onChange={setTab} className="mb-6" />

            {tab === "profile" && <ProfilePanel />}
            {tab === "files" && <FilesPanel />}
            {tab === "transcripts" && <TranscriptsPanel />}
            {tab === "clips" && <ClipsPanel />}
            {tab === "tasks" && <TasksPanel />}
            {tab === "llm-template" && <LlmTemplatePanel />}
            {tab === "advanced" && <AdvancedPanel />}
        </div>
    );
}
