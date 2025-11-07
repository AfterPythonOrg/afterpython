import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
  try {
    const blogPosts = await import('$static/blog/blog_posts.json');
    return {
      blogPosts: blogPosts.default,
    }
  } catch {
    return {
      blogPosts: [],
    };
  }
};