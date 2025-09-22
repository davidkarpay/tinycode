#!/usr/bin/env python3
"""
Test script for the plugin system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tiny_code.plugin_system import PluginManager
from tiny_code.agent import TinyCodeAgent

def test_plugin_system():
    """Test the plugin system functionality"""
    print("🔌 Testing TinyCode Plugin System")
    print("=" * 50)

    try:
        # Initialize plugin manager
        print("1. Initializing plugin manager...")
        agent = TinyCodeAgent()
        plugin_manager = PluginManager(agent=agent)
        print("   ✓ Plugin manager initialized")

        # Discover plugins
        print("\n2. Discovering plugins...")
        discovered = plugin_manager.discover_plugins()
        print(f"   ✓ Found {len(discovered)} plugins: {', '.join(discovered)}")

        # Load a plugin
        if "utilities" in discovered:
            print("\n3. Loading utilities plugin...")
            success = plugin_manager.load_plugin("utilities", enable=True)
            if success:
                print("   ✓ Utilities plugin loaded and enabled")
            else:
                print("   ✗ Failed to load utilities plugin")
                return False

            # Test plugin commands
            print("\n4. Testing plugin commands...")

            # Test hash command
            try:
                result = plugin_manager.execute_command("utilities:hash", "sha256", "hello world")
                print(f"   ✓ Hash command: {result[:50]}...")
            except Exception as e:
                print(f"   ✗ Hash command failed: {e}")

            # Test UUID command
            try:
                result = plugin_manager.execute_command("utilities:uuid", "v4")
                print(f"   ✓ UUID command: {result[:50]}...")
            except Exception as e:
                print(f"   ✗ UUID command failed: {e}")

            # Test timestamp command
            try:
                result = plugin_manager.execute_command("utilities:timestamp", "iso")
                print(f"   ✓ Timestamp command: {result[:50]}...")
            except Exception as e:
                print(f"   ✗ Timestamp command failed: {e}")

        # Test plugin info
        print("\n5. Testing plugin information...")
        info = plugin_manager.get_plugin_info("utilities")
        if info:
            print(f"   ✓ Plugin info retrieved: {info['name']} v{info['version']}")
            print(f"   ✓ Commands: {', '.join(info.get('commands', []))}")
        else:
            print("   ✗ Failed to get plugin info")

        # List all plugins
        print("\n6. Listing all plugins...")
        all_plugins = plugin_manager.list_plugins()
        for name, info in all_plugins.items():
            status = "enabled" if info.get('enabled') else "loaded" if info.get('loaded') else "available"
            print(f"   • {name}: {status}")

        print("\n🎉 Plugin system test completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Plugin system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_plugin_system()
    sys.exit(0 if success else 1)