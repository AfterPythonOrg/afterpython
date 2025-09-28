<script lang="ts">
  import { resolve } from '$app/paths';
  
  const { data } = $props();
</script>

<div>
  <a href={resolve(`/blog`)} class="back-to-blog">← Back to Blog</a>
  <h1>{data.post?.title}</h1>
  <p>{data.post?.excerpt}</p>
  <p>{data.post?.content}</p>
</div>