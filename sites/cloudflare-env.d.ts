declare module "cloudflare:workers" {
  export const env: {
    DB?: D1Database;
    FILES?: R2Bucket;
    PORTKEY_API_KEY?: string;
    PORTKEY_VIRTUAL_KEY?: string;
    PORTKEY_PROVIDER?: string;
    PORTKEY_BASE_URL?: string;
    PORTKEY_ENVIRONMENT?: string;
    OPENAI_API_KEY?: string;
    OPENAI_ANALYSIS_MODEL?: string;
    OPENAI_TURN_MODEL?: string;
    OPENAI_TRANSCRIBE_MODEL?: string;
  };
}
