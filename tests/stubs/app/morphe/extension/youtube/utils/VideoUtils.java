// Compile-only API stub and JVM test double. Never included in the extension DEX.
package app.morphe.extension.youtube.utils;

public final class VideoUtils {
    public static String lastVideo;
    public static boolean lastIntentRoute;
    public static boolean fail;

    public static void openVideo(String videoId, boolean intentRoute) {
        if (fail) throw new IllegalStateException("Test playback failure");
        lastVideo = videoId;
        lastIntentRoute = intentRoute;
    }
}
