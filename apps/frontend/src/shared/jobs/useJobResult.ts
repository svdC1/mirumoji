/**
 * @packageDocumentation A hook that applies a finished job's result: loads an
 * SRT or a converted video into the player (and routes there), or sends a
 * transcript to the dashboard. Works for a single-op job and for a batch child
 * (whose type is the single-op type). Shared by the task tray and the Tasks tab.
 */

import { useNavigate } from "react-router-dom";
import { usePlayer } from "@/contexts/PlayerContext";
import { staticUrl } from "@/shared/format/files";
import type { ConvertResult, Job, SrtResult } from "./types";

/**
 * Returns a function that applies a finished job's result.
 *
 * @returns {(job: Job) => void} The apply-result function.
 */
export function useJobResult(): (job: Job) => void {
    const player = usePlayer();
    const navigate = useNavigate();

    return (job: Job) => {
        const result = job.result;
        if (!result) return;
        if (job.type === "generate_srt" || job.type === "fix_srt") {
            const srt = result as unknown as SrtResult;
            const file = new File([srt.srt_content], "subtitles.srt", {
                type: "application/x-subrip",
            });
            player.setSrt(file);
            player.setSrtFileName(file.name);
            player.setSrtFileId(srt.srt_file_id);
            navigate("/player");
        } else if (job.type === "convert") {
            const conv = result as unknown as ConvertResult;
            // Load the converted MP4 as a tracked profile file, replacing any
            // device file or stale source id so later ops act on the MP4.
            player.setVideo(null);
            player.setVideoUrl(staticUrl(conv.video_url));
            player.setVideoFileName(conv.video_url.split("/").pop() ?? null);
            player.setVideoFileId(conv.file_id);
            navigate("/player");
        } else if (job.type === "transcribe") {
            navigate("/dashboard");
        }
    };
}
