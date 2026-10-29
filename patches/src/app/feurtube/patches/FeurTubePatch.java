// SPDX-License-Identifier: GPL-3.0-only
package app.feurtube.patches;

import app.morphe.patcher.extensions.InstructionExtensions;
import app.morphe.patcher.patch.BytecodePatch;
import app.morphe.patcher.patch.PatchKt;
import app.morphe.patcher.util.proxy.mutableTypes.MutableClass;
import app.morphe.patcher.util.proxy.mutableTypes.MutableMethod;
import app.morphe.patches.youtube.general.navigation.NavigationBarComponentsPatchKt;
import app.morphe.patches.youtube.shorts.components.ShortsComponentPatchKt;
import app.morphe.patches.youtube.shorts.startupshortsreset.ResumingShortsOnStartupPatchKt;
import com.android.tools.smali.dexlib2.immutable.ImmutableMethod;
import com.android.tools.smali.dexlib2.immutable.ImmutableMethodImplementation;
import com.android.tools.smali.dexlib2.iface.ClassDef;
import java.util.List;
import kotlin.Unit;

/** Desktop Morphe patch; all app-specific fingerprints belong to pinned RVX. */
public final class FeurTubePatch {
    public static final String POLICY = "Lapp/feurtube/extension/ShortsPolicy;";
    public static final String SETTING = "Lapp/morphe/extension/shared/settings/Setting;";
    public static final String SHORTS = "Lapp/morphe/extension/youtube/patches/shorts/ShortsPatch;";
    private static final InstructionExtensions INS = InstructionExtensions.INSTANCE;

    public static final BytecodePatch PATCH = PatchKt.bytecodePatch(
        "FeurTube policy", "Hide Shorts by default and open individual Shorts in the regular player.",
        false, builder -> {
            var shorts = ShortsComponentPatchKt.getShortsComponentPatch();
            builder.compatibleWith(shorts.getCompatibility().toArray(
                app.morphe.patcher.patch.Compatibility[]::new));
            builder.dependsOn(shorts,
                NavigationBarComponentsPatchKt.getNavigationBarComponentsPatch(),
                ResumingShortsOnStartupPatchKt.getResumingShortsOnStartupPatch());
            builder.extendWith(() -> FeurTubePatch.class.getResourceAsStream("/extensions/feurtube.dex"));
            builder.execute(context -> {
                requireMethod(context.classDefBy("Lapp/morphe/extension/youtube/utils/VideoUtils;"),
                    "openVideo", List.of("Ljava/lang/String;", "Z"), "V");
                requireMethod(context.classDefBy("Lapp/morphe/extension/youtube/patches/player/OpenVideosFullscreenHookPatch;"),
                    "setOpenNextVideoFullscreen", List.of("Ljava/lang/Boolean;"), "V");
                hookDefaults(context.mutableClassDefBy(SETTING));
                replaceShortsRedirect(context.mutableClassDefBy(SHORTS));
                return Unit.INSTANCE;
            });
            return Unit.INSTANCE;
        });

    public static void requireMethod(ClassDef type, String name, List<String> parameters, String returns) {
        for (var method : type.getMethods()) {
            if (method.getName().equals(name) && method.getParameterTypes().equals(parameters)
                    && method.getReturnType().equals(returns) && (method.getAccessFlags() & 0x8) != 0) return;
        }
        throw new IllegalStateException("Missing upstream static API: " + type.getType() + "->" + name);
    }

    public static void hookDefaults(MutableClass settings) {
        // Only the terminal constructor stores defaults and calls load().
        var parameters = List.of("Ljava/lang/String;", "Ljava/lang/Object;", "Z", "Z",
            "Ljava/lang/String;", SETTING.substring(0, SETTING.length() - 1) + "$Availability;",
            SETTING.substring(0, SETTING.length() - 1) + "$SliderConfig;");
        var matches = settings.getMethods().stream().filter(method ->
            method.getName().equals("<init>") && method.getParameterTypes().equals(parameters)).toList();
        if (matches.size() != 1) {
            throw new IllegalStateException("Expected one upstream Setting constructor; got " + matches.size());
        }
        INS.addInstructions(matches.getFirst(), 0,
            "invoke-static/range {p1 .. p2}, " + POLICY
                + "->defaultValue(Ljava/lang/String;Ljava/lang/Object;)Ljava/lang/Object;\n"
                + "move-result-object p2");
    }

    public static void replaceShortsRedirect(MutableClass shorts) {
        var matches = shorts.getMethods().stream().filter(method ->
            method.getName().equals("openShortInRegularPlayer")
                && method.getParameterTypes().equals(List.of("Ljava/lang/String;"))
                && method.getReturnType().equals("Z")).toList();
        if (matches.size() != 1) {
            throw new IllegalStateException("Expected one upstream Shorts redirect; got " + matches.size());
        }
        var original = matches.getFirst();
        var replacement = new MutableMethod(new ImmutableMethod(original.getDefiningClass(),
            original.getName(), original.getParameters(), original.getReturnType(),
            original.getAccessFlags(), original.getAnnotations(), original.getHiddenApiRestrictions(),
            new ImmutableMethodImplementation(2, List.of(), List.of(), List.of())));
        // Modified from RVX ShortsPatch.openShortInRegularPlayer. Retain its regular-player
        // route, but consume empty-ID launches and remove its selected-Shorts-tab exemption.
        // Original authors: anddea, inotia00 and Morphe contributors. See NOTICE.
        INS.addInstructions(replacement, 0, """
            invoke-static {p0}, Lapp/feurtube/extension/ShortsPolicy;->openShort(Ljava/lang/String;)Z
            move-result v0
            return v0
            """);
        shorts.getMethods().remove(original);
        shorts.getMethods().add(replacement);
    }
}
