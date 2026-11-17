import { z } from "zod";

export const IndustrySchema = z
  .object({ name: z.string(), slug: z.string() })
  .strict();

export const BrandSchema = z
  .object({
    name: z.string(),
    slug: z.string(),
    industry: IndustrySchema.nullable(),
    average_rating: z.number().min(1).max(5).nullable(),
    review_count: z.number().int().nonnegative(),
    short_description: z.string(),
    top_review_snippet: z.string().nullable(),
  })
  .strict();

export const PageSchema = z
  .object({
    count: z.number().int().nonnegative(),
    page: z.number().int().positive(),
    page_size: z.number().int().positive(),
    total_pages: z.number().int().nonnegative(),
    next: z.number().int().positive().nullable(),
    previous: z.number().int().positive().nullable(),
    results: z.array(BrandSchema),
    industries: z.array(IndustrySchema),
  })
  .strict();

export const ReviewSchema = z
  .object({
    name: z.string(),
    slug: z.string(),
    brand_name: z.string(),
    brand_slug: z.string(),
    reviewer_name: z.string(),
    reviewer_location: z.string(),
    rating: z.number().int().min(1).max(5),
    body: z.string(),
    published_at: z.string().datetime({ offset: true }),
  })
  .strict();

export const DetailSchema = z
  .object({
    name: z.string(),
    slug: z.string(),
    industry: IndustrySchema.nullable(),
    average_rating: z.number().min(1).max(5).nullable(),
    review_count: z.number().int().nonnegative(),
    short_description: z.string(),
    body: z.string(),
    website_url: z.string(),
    founded_year: z.number().int().nullable(),
    headquarters: z.string(),
    reviews: z.array(ReviewSchema),
  })
  .strict();

export const RecentSchema = z
  .object({ reviews: z.array(ReviewSchema) })
  .strict();

export const PatchSchema = z
  .object({ short_description: z.string().trim().min(1).max(500) })
  .strict();

export type Brand = z.infer<typeof BrandSchema>;
export type Industry = z.infer<typeof IndustrySchema>;
export type BrandPage = z.infer<typeof PageSchema>;
export type Review = z.infer<typeof ReviewSchema>;
export type BrandDetail = z.infer<typeof DetailSchema>;
