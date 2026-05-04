import type { PageServerLoad } from './$types';

export const prerender = true;

type FaqItem = {
	question: string;
	answer: string;
	category?: string;
};

export const load: PageServerLoad = async () => {
	try {
		const faq = await import('$static/faq.json');
		return { faq: (faq.default ?? faq) as FaqItem[] };
	} catch {
		return { faq: [] as FaqItem[] };
	}
};
