<script lang="ts">
	type LogoProps = {
		class?: string;
		size?: 'sm' | 'md' | 'lg' | 'xl';
	}

	let { class: className = '', size = 'md' }: LogoProps = $props();

	let hasLogo = $state(true);

	// Size classes
	const sizeClasses = {
		sm: 'h-10',
		md: 'h-14',
		lg: 'h-18',
		xl: 'h-22'
	};

	// Handle fallback to different image formats
	function handleImageError(event: Event) {
		const img = event.target as HTMLImageElement;
		const currentSrc = img.src;

		// Try formats in priority order: svg -> png -> jpg -> jpeg
		if (currentSrc.endsWith('/logo.svg')) {
			img.src = '/logo.png';
		} else if (currentSrc.endsWith('/logo.png')) {
			img.src = '/logo.jpg';
		} else if (currentSrc.endsWith('/logo.jpg')) {
			img.src = '/logo.jpeg';
		} else {
			// All formats failed, hide the logo
			hasLogo = false;
		}
	}
</script>

{#if hasLogo}
	<a href="/" class="flex items-center {className}">
		<img
			src="/logo.svg"
			alt="Logo"
			class="{sizeClasses[size]} w-auto"
			onerror={handleImageError}
		/>
	</a>
{/if}
