package ink;

import net.minecraftforge.common.ForgeConfigSpec;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.event.config.ModConfigEvent;

// Charge automatiquement la config COMMON du mod et la garde synchronisee
@Mod.EventBusSubscriber(modid = Ink.MODID, bus = Mod.EventBusSubscriber.Bus.MOD)
public class Config {

    private static final ForgeConfigSpec.Builder BUILDER = new ForgeConfigSpec.Builder();

    public static final ForgeConfigSpec.BooleanValue EXAMPLE_ENABLED = BUILDER
            .comment("Exemple d'option booleenne")
            .define("exampleEnabled", true);

    static final ForgeConfigSpec SPEC = BUILDER.build();

    public static boolean exampleEnabled;

    @SubscribeEvent
    static void onLoad(final ModConfigEvent event) {
        exampleEnabled = EXAMPLE_ENABLED.get();
    }
}
