import { mdsvex } from 'mdsvex';
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

const outputDir = "build";

const config = {
	preprocess: [vitePreprocess(), mdsvex()],
	kit: { 
		adapter: adapter({
			// default options are shown. On some platforms
			// these options are set automatically — see below
			pages: outputDir,
			assets: outputDir,
			fallback: '200.html', // may differ from host to host
			precompress: false,
			strict: true,
		}),
		alias: {
			// '@': 'src/',
			'$components': 'src/lib/components/',
			'$static': 'static/',
		},
	},
	extensions: ['.svelte', '.svx']
};

export default config;
