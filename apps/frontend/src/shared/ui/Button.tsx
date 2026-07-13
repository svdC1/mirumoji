/**
 * @packageDocumentation Button primitive with variants, sizes, and a loading state.
 */

import React from "react";
import { cn } from "./cn";
import { Spinner } from "./Spinner";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

const BASE =
    "inline-flex items-center justify-center gap-2 rounded-control font-medium transition-colors select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-shu/60 disabled:opacity-50 disabled:pointer-events-none";

const VARIANTS: Record<ButtonVariant, string> = {
    primary: "bg-shu text-ink hover:bg-shu-soft",
    secondary: "border border-ink/10 bg-surface-2 text-ink hover:border-ink/20 hover:bg-ink/5",
    ghost: "text-ink-muted hover:text-ink hover:bg-ink/5",
    danger: "bg-danger text-ink hover:bg-danger/85",
};

const SIZES: Record<ButtonSize, string> = {
    sm: "h-8 px-3 text-sm",
    md: "h-10 px-4 text-sm",
    lg: "h-11 px-5 text-base",
};

/**
 * Returns the button utility classes for a variant/size, so non-`<button>`
 * elements (e.g. React Router `<Link>`) can share the same look.
 */
export function buttonClasses(
    variant: ButtonVariant = "primary",
    size: ButtonSize = "md",
    className?: string
): string {
    return cn(BASE, VARIANTS[variant], SIZES[size], className);
}

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: ButtonVariant;
    size?: ButtonSize;
    loading?: boolean;
}

/**
 * The primary action button. `loading` shows a spinner and disables the button.
 */
export function Button({
    variant = "primary",
    size = "md",
    loading = false,
    className,
    children,
    disabled,
    ...rest
}: ButtonProps) {
    return (
        <button
            className={buttonClasses(variant, size, className)}
            disabled={disabled || loading}
            {...rest}
        >
            {loading && <Spinner className="h-4 w-4" />}
            {children}
        </button>
    );
}
