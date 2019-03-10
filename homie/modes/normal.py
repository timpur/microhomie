from homie.modules.network import NetworkModule
from homie.modules.mqtt import MQTTModule
from homie.modules.convention import ConventionModule
# from homie.modules.configuration import ConfigurationModule


MODE_NORMAL = [
    # ConfigurationModule,
    NetworkModule,
    MQTTModule,
    ConventionModule
]
