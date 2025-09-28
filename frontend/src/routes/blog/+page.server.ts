import type { PageServerLoad } from './$types';
import blogPosts from '$static/blog/blog_posts.json';

export const load: PageServerLoad = () => {
  return {
    blogPosts,
  };
};