/**
 * @packageDocumentation Preloads the demo's sample episode into the player on
 * startup, so the tour opens on a ready-to-watch video. Reads the committed
 * `sample.json` descriptor; a no-op until the generator fills it.
 */

import { useEffect } from "react";
import { usePlayer } from "@real/contexts/PlayerContext";
import { staticUrl } from "@/shared/format/files";
import sample from "./generated/sample.json";

interface SampleManifest {
    video?: { url: string; name: string; fileId?: string };
    srt?: { url: string; name: string; fileId?: string };
}

/** Loads the sample video + subtitles into the player once, on mount. */
export function DemoBootstrap() {
    const player = usePlayer();

    useEffect(() => {
        const s = sample as SampleManifest;
        if (!s.video) return;

        player.setVideoUrl(staticUrl(s.video.url));
        player.setVideoFileName(s.video.name);
        player.setVideoFileId(s.video.fileId ?? null);

        const srt = s.srt;
        if (srt) {
            fetch(staticUrl(srt.url))
                .then((r) => r.text())
                .then((text) => {
                    player.setSrt(new File([text], srt.name, { type: "text/plain" }));
                    player.setSrtFileName(srt.name);
                    player.setSrtFileId(srt.fileId ?? null);
                })
                .catch(() => {
                    /* the sample SRT asset is missing; leave the player video-only */
                });
        }
        // Preload once on mount.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return null;
}
