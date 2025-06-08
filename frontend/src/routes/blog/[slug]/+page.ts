import blogPosts from '$lib/blog_posts.json';

export const prerender = true;

// This function tells SvelteKit which [slug] values to prerender
export async function entries() {
  // Use the imported JSON directly instead of fetching
  return blogPosts.map((post: any) => ({
    slug: post.slug
  }));
} 