package ink;

import com.mojang.logging.LogUtils;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.ModLoadingContext;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.config.ModConfig;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import net.minecraftforge.event.server.ServerStartingEvent;
import org.slf4j.Logger;

// La valeur ci-dessous doit correspondre a l'entree modId de META-INF/mods.toml
@Mod(Ink.MODID)
public class Ink {

    // Identifiant du mod, reference partout ailleurs
    public static final String MODID = "inkmachine";

    private static final Logger LOGGER = LogUtils.getLogger();

    public Ink() {
        IEventBus modEventBus = FMLJavaModLoadingContext.get().getModEventBus();

        // Enregistrement des methodes de cycle de vie du chargement
        modEventBus.addListener(this::commonSetup);

        // On s'abonne aux evenements du bus principal (serveur, jeu, ...)
        MinecraftForge.EVENT_BUS.register(this);

        // Enregistrement du fichier de configuration du mod
        ModLoadingContext.get().registerConfig(ModConfig.Type.COMMON, Config.SPEC);
    }

    private void commonSetup(final FMLCommonSetupEvent event) {
        LOGGER.info("[{}] setup commun", MODID);
        LOGGER.info("[{}] option d'exemple = {}", MODID, Config.exampleEnabled);
    }

    @SubscribeEvent
    public void onServerStarting(ServerStartingEvent event) {
        LOGGER.info("[{}] le serveur demarre", MODID);
    }
}
