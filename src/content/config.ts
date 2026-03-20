import { defineCollection, z } from 'astro:content';

const blog = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.string(),
    tags: z.array(z.string()),
    hexagram: z.string().optional(),
    element: z.string().optional(),
  }),
});

const scriptures = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    chapter: z.number().optional(),
  }),
});

export const collections = {
  blog,
  scriptures,
};
