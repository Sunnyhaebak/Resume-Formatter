import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "ResumeTailor AI - One-Page LaTeX Resume Engine",
    short_name: "ResumeTailor",
    description:
      "Truthful, AI-powered LaTeX resume tailoring engine strictly fit for single-page ATS perfection.",
    start_url: "/",
    display: "standalone",
    background_color: "#0f172a",
    theme_color: "#1B365D",
    icons: [
      {
        src: "/icon-192x192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "maskable",
      },
      {
        src: "/icon-512x512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
    ],
    // Web Share Target API for Android sharing from LinkedIn/Naukri
    share_target: {
      action: "/",
      method: "GET",
      params: {
        title: "title",
        text: "jd",
        url: "url",
      },
    } as any,
  };
}
