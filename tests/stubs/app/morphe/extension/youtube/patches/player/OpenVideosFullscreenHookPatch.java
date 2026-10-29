// Compile-only API stub and JVM test double. Never included in the extension DEX.
package app.morphe.extension.youtube.patches.player;

public final class OpenVideosFullscreenHookPatch {
    public static Boolean fullscreen;

    public static void setOpenNextVideoFullscreen(Boolean value) {
        fullscreen = value;
    }
}
