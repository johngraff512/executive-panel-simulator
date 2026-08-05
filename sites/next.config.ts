import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The Site uses small bundled brand and executive images. Serving them
  // directly avoids an unavailable local ASSETS image-optimization binding.
  images: {
    unoptimized: true,
  },
  experimental: {
    // Vinext applies this limit to multipart POST requests, including route
    // handlers. Leave enough envelope room for the route's 50 MB PDF limit.
    serverActions: {
      bodySizeLimit: "52mb",
    },
  },
};

export default nextConfig;
