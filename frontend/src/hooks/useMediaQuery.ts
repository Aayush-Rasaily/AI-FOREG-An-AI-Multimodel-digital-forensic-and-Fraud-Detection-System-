import { useEffect, useState } from "react";

/**
 * Phase 11B breakpoints:
 * - mobile:  < 640px
 * - tablet:  640–1024px
 * - laptop:  1024–1440px
 * - desktop: > 1440px
 */
export const BREAKPOINTS = {
  tablet: "(min-width: 640px)",
  laptop: "(min-width: 1024px)",
  desktop: "(min-width: 1440px)",
  reduceMotion: "(prefers-reduced-motion: reduce)",
} as const;

export function useMediaQuery(query: string, defaultValue = false): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window === "undefined" || !window.matchMedia) {
      return defaultValue;
    }
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    if (!window.matchMedia) {
      return;
    }
    const media = window.matchMedia(query);
    const onChange = () => setMatches(media.matches);
    onChange();
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [query]);

  return matches;
}

export function useViewport() {
  const isTabletUp = useMediaQuery(BREAKPOINTS.tablet);
  const isLaptopUp = useMediaQuery(BREAKPOINTS.laptop);
  const isDesktop = useMediaQuery(BREAKPOINTS.desktop);
  const reduceMotion = useMediaQuery(BREAKPOINTS.reduceMotion);

  return {
    isMobile: !isTabletUp,
    isTablet: isTabletUp && !isLaptopUp,
    isLaptop: isLaptopUp && !isDesktop,
    isDesktop,
    isTabletUp,
    isLaptopUp,
    reduceMotion,
  };
}
