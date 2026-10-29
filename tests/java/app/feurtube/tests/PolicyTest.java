// SPDX-License-Identifier: GPL-3.0-only
package app.feurtube.tests;

import app.feurtube.extension.ShortsPolicy;
import app.feurtube.patches.FeurTubePatch;
import app.morphe.extension.youtube.utils.VideoUtils;
import app.morphe.extension.youtube.patches.player.OpenVideosFullscreenHookPatch;
import app.morphe.patcher.util.proxy.mutableTypes.MutableClass;
import com.android.tools.smali.dexlib2.Opcodes;
import com.android.tools.smali.dexlib2.Opcode;
import com.android.tools.smali.dexlib2.dexbacked.DexBackedDexFile;
import com.android.tools.smali.dexlib2.immutable.ImmutableDexFile;
import com.android.tools.smali.dexlib2.iface.ClassDef;
import com.android.tools.smali.dexlib2.iface.Method;
import com.android.tools.smali.dexlib2.iface.instruction.ReferenceInstruction;
import com.android.tools.smali.dexlib2.iface.reference.MethodReference;
import com.android.tools.smali.dexlib2.writer.pool.DexPool;
import java.io.FileInputStream;
import java.nio.ByteBuffer;
import java.util.List;
import java.util.zip.ZipFile;

public final class PolicyTest {
    private enum Player { SHORTS_PLAYER, REGULAR_PLAYER, REGULAR_PLAYER_FULLSCREEN }

    public static void main(String[] args) throws Exception {
        for (String key : List.of("navigation_shorts_button", "shorts_shelf", "shorts_shelf_channel",
                "shorts_shelf_home_related_videos", "shorts_shelf_search", "shorts_shelf_subscriptions",
                "shorts_shelf_video_description", "shorts_shelf_history", "shorts_floating_button")) {
            assert ShortsPolicy.defaultValue("revanced_hide_" + key, false).equals(true) : key;
        }
        assert ShortsPolicy.defaultValue("revanced_disable_resuming_shorts_player", false).equals(true);
        assert ShortsPolicy.defaultValue("revanced_shorts_player_type", Player.SHORTS_PLAYER) == Player.REGULAR_PLAYER;
        Object sentinel = new Object();
        assert ShortsPolicy.defaultValue("unrelated_setting", sentinel) == sentinel;
        assert ShortsPolicy.defaultValue("revanced_restore_old_settings_menus", false).equals(false);
        assert ShortsPolicy.defaultValue("morphe_spoof_video_streams", true).equals(false);
        assert ShortsPolicy.defaultValue("revanced_spoof_streaming_data", true).equals(false);
        assert ShortsPolicy.openShort(null);
        assert ShortsPolicy.openShort("");
        assert VideoUtils.lastVideo == null;
        assert ShortsPolicy.openShort("testVideoId");
        assert VideoUtils.lastVideo.equals("testVideoId");
        assert VideoUtils.lastIntentRoute;
        assert Boolean.FALSE.equals(OpenVideosFullscreenHookPatch.fullscreen);
        VideoUtils.fail = true;
        var stderr = System.err;
        var errors = new java.io.ByteArrayOutputStream();
        try {
            System.setErr(new java.io.PrintStream(errors));
            assert ShortsPolicy.openShort("testVideoId");
        } finally {
            System.setErr(stderr);
        }
        assert errors.toString().contains("could not open Short");

        DexBackedDexFile dex;
        try (var zip = new ZipFile(args[0]); var stream = zip.getInputStream(zip.getEntry("extensions/shared.mpe"))) {
            dex = new DexBackedDexFile(Opcodes.getDefault(), ByteBuffer.wrap(stream.readAllBytes()));
        }
        var settings = new MutableClass(find(dex, FeurTubePatch.SETTING));
        var shorts = new MutableClass(find(dex, FeurTubePatch.SHORTS));
        FeurTubePatch.requireMethod(find(dex, "Lapp/morphe/extension/youtube/utils/VideoUtils;"),
            "openVideo", List.of("Ljava/lang/String;", "Z"), "V");
        FeurTubePatch.requireMethod(find(dex, "Lapp/morphe/extension/youtube/patches/player/OpenVideosFullscreenHookPatch;"),
            "setOpenNextVideoFullscreen", List.of("Ljava/lang/Boolean;"), "V");
        FeurTubePatch.hookDefaults(settings);
        FeurTubePatch.replaceShortsRedirect(shorts);
        long hooks = settings.getMethods().stream().filter(m -> calls(m, FeurTubePatch.POLICY, "defaultValue")).count();
        assert hooks == 1 : "Must hook only the terminal constructor";
        Method redirect = shorts.getMethods().stream().filter(m -> m.getName().equals("openShortInRegularPlayer")).findFirst().orElseThrow();
        assert calls(redirect, FeurTubePatch.POLICY, "openShort");
        assert !calls(redirect, "Lapp/morphe/extension/youtube/shared/NavigationBar$NavigationButton;", "getSelectedNavigationButton");
        assert java.util.stream.StreamSupport.stream(
            redirect.getImplementation().getInstructions().spliterator(), false).count() == 3;
        for (var instruction : redirect.getImplementation().getInstructions()) {
            // There must be no return-false path back into the Shorts feed.
            if (instruction.getOpcode() == Opcode.RETURN) {
                assert ((com.android.tools.smali.dexlib2.iface.instruction.OneRegisterInstruction) instruction).getRegisterA() == 0;
            }
        }
        DexPool.writeTo(args[1], new ImmutableDexFile(Opcodes.getDefault(), List.of(settings, shorts)));
        try (var input = new FileInputStream(args[1])) {
            var roundtrip = new DexBackedDexFile(Opcodes.getDefault(), ByteBuffer.wrap(input.readAllBytes()));
            assert roundtrip.getClasses().size() == 2;
        }
        try (var input = new FileInputStream(args[2])) {
            var extension = new DexBackedDexFile(Opcodes.getDefault(), ByteBuffer.wrap(input.readAllBytes()));
            assert extension.getClasses().size() == 1 : "Test stubs must not be injected";
            var policy = find(extension, FeurTubePatch.POLICY);
            Method open = java.util.stream.StreamSupport.stream(policy.getMethods().spliterator(), false)
                .filter(m -> m.getName().equals("openShort")).findFirst().orElseThrow();
            assert open.getImplementation().getTryBlocks().size() == 1;
        }
        try {
            FeurTubePatch.hookDefaults(shorts);
            throw new AssertionError("Missing upstream constructor must fail patching");
        } catch (IllegalStateException expected) {
            assert expected.getMessage().contains("Expected one");
        }
        System.out.println("Policy defaults and released upstream DEX mutation tests passed");
    }

    private static ClassDef find(DexBackedDexFile dex, String type) {
        return dex.getClasses().stream().filter(c -> c.getType().equals(type)).findFirst().orElseThrow();
    }

    private static boolean calls(Method method, String type, String name) {
        if (method.getImplementation() == null) return false;
        for (var instruction : method.getImplementation().getInstructions()) {
            if (instruction instanceof ReferenceInstruction ref && ref.getReference() instanceof MethodReference call
                    && call.getDefiningClass().equals(type) && call.getName().equals(name)) return true;
        }
        return false;
    }
}
