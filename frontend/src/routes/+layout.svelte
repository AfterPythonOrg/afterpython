<script lang="ts">
	import '../app.css';
	import { resolve } from '$app/paths';

	let { children } = $props();
</script>

<nav>
	<a href={resolve('/')}>Home</a>
	<a href={resolve('/blog')}>Blog</a>
</nav>
{@render children()}
