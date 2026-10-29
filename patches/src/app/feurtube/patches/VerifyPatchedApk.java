// SPDX-License-Identifier: GPL-3.0-only
package app.feurtube.patches;

import com.android.tools.smali.dexlib2.Opcodes;
import com.android.tools.smali.dexlib2.dexbacked.DexBackedDexFile;
import com.android.tools.smali.dexlib2.iface.ClassDef;
import com.android.tools.smali.dexlib2.iface.instruction.ReferenceInstruction;
import com.android.tools.smali.dexlib2.iface.reference.MethodReference;
import java.nio.ByteBuffer;
import java.util.HashMap;
import java.util.List;
import java.util.zip.ZipFile;

public final class VerifyPatchedApk {
    public static void main(String[] args) throws Exception {
        var found = new HashMap<String, ClassDef>();
        var wanted = List.of(FeurTubePatch.POLICY, FeurTubePatch.SETTING, FeurTubePatch.SHORTS);
        try (var zip = new ZipFile(args[0])) {
            for (var entry : zip.stream().filter(e -> e.getName().matches("classes(?:[0-9]+)?\\.dex")).toList()) {
                try (var input = zip.getInputStream(entry)) {
                    var dex = new DexBackedDexFile(Opcodes.getDefault(), ByteBuffer.wrap(input.readAllBytes()));
                    for (var type : dex.getClasses()) {
                        if (wanted.contains(type.getType())) found.put(type.getType(), type);
                        if (type.getType().startsWith("Lapp/feurtube/") && !type.getType().equals(FeurTubePatch.POLICY)) {
                            throw new IllegalStateException("Unexpected FeurTube runtime class: " + type.getType());
                        }
                    }
                }
            }
        }
        if (!found.keySet().containsAll(wanted)) throw new IllegalStateException("Missing FeurTube runtime classes");
        if (!calls(found.get(FeurTubePatch.SETTING), "<init>", "defaultValue")
                || !calls(found.get(FeurTubePatch.SHORTS), "openShortInRegularPlayer", "openShort")) {
            throw new IllegalStateException("Rebuilt APK is missing the FeurTube hooks");
        }
        System.out.println("Verified FeurTube defaults and Shorts redirect hooks in rebuilt APK");
    }

    private static boolean calls(ClassDef type, String methodName, String target) {
        for (var method : type.getMethods()) {
            if (!method.getName().equals(methodName) || method.getImplementation() == null) continue;
            for (var instruction : method.getImplementation().getInstructions()) {
                if (instruction instanceof ReferenceInstruction ref && ref.getReference() instanceof MethodReference call
                        && call.getDefiningClass().equals(FeurTubePatch.POLICY) && call.getName().equals(target)) return true;
            }
        }
        return false;
    }
}
