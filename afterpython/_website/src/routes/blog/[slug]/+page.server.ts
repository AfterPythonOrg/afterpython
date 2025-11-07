/**
 * #TODO: use prerender.entries, see https://svelte.dev/docs/kit/page-options#entries
 * export const prerender = true;
 */

import type { PageServerLoad } from './$types';
import blogPosts from '$static/blog/blog_posts.json';

export const load: PageServerLoad = ({ params }) => {
  const { slug } = params;
  const post = blogPosts.find((post) => post.slug === slug);
  return { post };
};