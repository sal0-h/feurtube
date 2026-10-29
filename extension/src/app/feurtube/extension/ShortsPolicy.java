// SPDX-License-Identifier: GPL-3.0-only
package app.feurtube.extension;

import app.morphe.extension.youtube.patches.player.OpenVideosFullscreenHookPatch;
import app.morphe.extension.youtube.utils.VideoUtils;

/** Defaults applied before an upstream Setting loads its saved preference. */
public final class ShortsPolicy {
    private ShortsPolicy() {}

    public static Object defaultValue(String key, Object original) {
        switch (key) {
            case "morphe_spoof_video_streams":
            case "revanced_spoof_streaming_data":
                // Preserve the stock playback client first, including Premium capabilities.
                // Users may enable the upstream workaround if stock playback fails.
                return Boolean.FALSE;
            case "revanced_hide_navigation_shorts_button":
            case "revanced_hide_shorts_shelf":
            case "revanced_hide_shorts_shelf_channel":
            case "revanced_hide_shorts_shelf_home_related_videos":
            case "revanced_hide_shorts_shelf_search":
            case "revanced_hide_shorts_shelf_subscriptions":
            case "revanced_hide_shorts_shelf_video_description":
            case "revanced_hide_shorts_shelf_history":
            case "revanced_hide_shorts_floating_button":
            case "revanced_disable_resuming_shorts_player":
                return Boolean.TRUE;
            case "revanced_shorts_player_type":
                return regularPlayer(original);
            default:
                return original;
        }
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    private static Object regularPlayer(Object original) {
        // Avoid linking the extension to an upstream enum at compile time.
        return Enum.valueOf(((Enum) original).getDeclaringClass(), "REGULAR_PLAYER");
    }

    public static boolean openShort(String videoId) {
        if (videoId == null || videoId.isEmpty()) return true;
        try {
            OpenVideosFullscreenHookPatch.setOpenNextVideoFullscreen(Boolean.FALSE);
            // RVX uses vnd.youtube:// for this flag, avoiding re-entry via /shorts/.
            VideoUtils.openVideo(videoId, true);
        } catch (Exception exception) {
            System.err.println("FeurTube: could not open Short in regular player");
            exception.printStackTrace();
        }
        // Consume the Shorts navigation even when opening the regular player fails.
        return true;
    }
}
