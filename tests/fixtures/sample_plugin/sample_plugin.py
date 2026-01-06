from configurator.plugins.base import PluginBase, PluginInfo


class SamplePlugin(PluginBase):
    plugin_info = PluginInfo(
        name="sample-plugin",
        version="1.0.0",
        description="A sample plugin for testing",
    )

    def validate(self) -> bool:
        return True

    def configure(self) -> bool:
        print("Sample Plugin Configured!")
        return True

    def verify(self) -> bool:
        return True
