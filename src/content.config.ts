import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

const projects = defineCollection({
  loader: glob({ base: "./src/content/projects", pattern: "**/*.md" }),
  schema: z.object({
    title: z.string(),
    summary: z.string(),
    focusAreas: z.array(z.string()),
    azureServices: z.array(z.string()),
    status: z.string(),
  }),
});

export const collections = { projects };
