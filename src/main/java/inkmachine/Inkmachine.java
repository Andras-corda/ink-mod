package inkmachine;

import com.mojang.logging.LogUtils;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.ModLoadingContext;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.config.ModConfig;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.slf4j.Logger;

// La valeur ci-dessous doit correspondre a l'entree modId de META-INF/mods.toml
@Mod(Inkmachine.MODID)
public class Inkmachine {

    // Identifiant du mod, reference partout ailleurs
    public static final String MODID = "inkmachine";

    private static final Logger LOGGER = LogUtils.getLogger();

    public Inkmachine() {
        IEventBus modEventBus = FMLJavaModLoadingContext.get().getModEventBus();

        modEventBus.addListener(this::commonSetup);

        MinecraftForge.EVENT_BUS.register(this);

        ModLoadingContext.get().registerConfig(ModConfig.Type.COMMON, Config.SPEC);
    }

    private void commonSetup(final FMLCommonSetupEvent event) {
        LOGGER.info("[{}] setup commun", MODID);
        LOGGER.info("[{}] option d'exemple = {}", MODID, Config.exampleEnabled);
    }
}
