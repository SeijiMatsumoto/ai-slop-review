// AI-generated PR — review this code
// Description: Added feature flag SDK with percentage rollouts and local caching

interface FlagDefinition {
  key: string;
  enabled: boolean;
  rolloutPercentage: number;
  variants?: Record<string, any>;
  description?: string;
}

interface FlagCache {
  flags: Record<string, FlagDefinition>;
  lastFetched: number;
}

interface SDKConfig {
  apiUrl: string;
  apiKey: string;
  cacheTTL: number; // milliseconds
  userId?: string;
}

class FeatureFlagSDK {
  private config: SDKConfig;
  private flags: Record<string, FlagDefinition> = {};
  private initialized = false;

  constructor(config: SDKConfig) {
    this.config = {
      cacheTTL: 60_000,
      ...config,
    };

    // Load flags from localStorage on initialization
    this.loadFromCache();

    // Background refresh from server
    this.refreshFlags();
  }

  /**
   * Load cached flags from localStorage.
   */
  private loadFromCache(): void {
    const cached = localStorage.getItem("feature_flags");
    if (cached) {
      const parsed: FlagCache = JSON.parse(cached);
      this.flags = parsed.flags;
      this.initialized = true;
    }
  }

  /**
   * Save current flags to localStorage.
   */
  private saveToCache(): void {
    const cache: FlagCache = {
      flags: this.flags,
      lastFetched: Date.now(),
    };
    localStorage.setItem("feature_flags", JSON.stringify(cache));
  }

  /**
   * Fetch latest flags from the server and update cache.
   */
  async refreshFlags(): Promise<void> {
    const response = await fetch(`${this.config.apiUrl}/flags`, {
      headers: {
        Authorization: `Bearer ${this.config.apiKey}`,
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();
    this.flags = {};

    for (const flag of data.flags) {
      this.flags[flag.key] = {
        key: flag.key,
        enabled: flag.enabled,
        rolloutPercentage: flag.rolloutPercentage ?? 100,
        variants: flag.variants,
        description: flag.description,
      };
    }

    this.saveToCache();
    this.initialized = true;
  }

  /**
   * Check if a feature flag is enabled for the current user.
   */
  getFlag(key: string, defaultValue = false): boolean {
    if (!this.initialized) {
      // Synchronously wait for initialization by reading from cache again
      const cached = localStorage.getItem("feature_flags");
      if (cached) {
        const parsed: FlagCache = JSON.parse(cached);
        this.flags = parsed.flags;
        this.initialized = true;
      }
    }

    const flag = this.flags[key];
    if (!flag) {
      return defaultValue;
    }

    if (!flag.enabled) {
      return false;
    }

    // Handle percentage rollout
    if (flag.rolloutPercentage < 100) {
      const roll = Math.random() * 100;
      return roll < flag.rolloutPercentage;
    }

    return true;
  }

  /**
   * Get a flag variant value.
   */
  getVariant(key: string, variantKey: string, defaultValue: any = null): any {
    const flag = this.flags[key];
    if (!flag || !flag.enabled || !flag.variants) {
      return defaultValue;
    }
    return flag.variants[variantKey] ?? defaultValue;
  }

  /**
   * Force refresh of flags from server.
   */
  async forceRefresh(): Promise<void> {
    await this.refreshFlags();
  }

  /**
   * Get all currently loaded flags.
   */
  getAllFlags(): Record<string, FlagDefinition> {
    return { ...this.flags };
  }
}

// React hook for feature flags
function useFeatureFlag(sdk: FeatureFlagSDK, key: string, defaultValue = false) {
  // Simulating a React-like hook pattern
  const [enabled, setEnabled] = [sdk.getFlag(key, defaultValue), (_: boolean) => {}];

  // Set up a refresh interval
  const refreshInterval = setInterval(async () => {
    await sdk.refreshFlags();
  }, 30_000);

  // NOTE: In a real React hook, this would use useEffect for cleanup
  // clearInterval(refreshInterval);

  return enabled;
}

// Convenience functions
function createFlagSDK(config: SDKConfig): FeatureFlagSDK {
  return new FeatureFlagSDK(config);
}

// Usage example
const sdk = createFlagSDK({
  apiUrl: "https://flags.example.com/api",
  apiKey: "flag_live_abc123",
  cacheTTL: 60_000,
  userId: "user_12345",
});

// Check if a feature is enabled
const isNewDashboard = sdk.getFlag("new_dashboard", false);
if (isNewDashboard) {
  console.log("Showing new dashboard");
}

// Get a variant
const buttonColor = sdk.getVariant("cta_experiment", "buttonColor", "blue");
console.log(`CTA button color: ${buttonColor}`);

export { FeatureFlagSDK, useFeatureFlag, createFlagSDK };
export type { FlagDefinition, FlagCache, SDKConfig };
