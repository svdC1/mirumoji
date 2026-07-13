/**
 * @packageDocumentation Form field primitives (Input, Select, Label, and Field).
 */

import React from "react";
import { cn } from "./cn";
import { controlClasses } from "./control";

export const Input = React.forwardRef<
    HTMLInputElement,
    React.InputHTMLAttributes<HTMLInputElement>
>(function Input({ className, ...rest }, ref) {
    return <input ref={ref} className={cn(controlClasses, className)} {...rest} />;
});

export const Select = React.forwardRef<
    HTMLSelectElement,
    React.SelectHTMLAttributes<HTMLSelectElement>
>(function Select({ className, children, ...rest }, ref) {
    return (
        <select ref={ref} className={cn(controlClasses, "cursor-pointer", className)} {...rest}>
            {children}
        </select>
    );
});

export type LabelProps = React.LabelHTMLAttributes<HTMLLabelElement>;

export function Label({ className, ...rest }: LabelProps) {
    return (
        <label
            className={cn("mb-1.5 block text-sm font-medium text-ink-muted", className)}
            {...rest}
        />
    );
}

export interface FieldProps {
    label?: React.ReactNode;
    htmlFor?: string;
    hint?: React.ReactNode;
    className?: string;
    children: React.ReactNode;
}

/**
 * A labelled form row: optional label + control + optional hint.
 */
export function Field({ label, htmlFor, hint, className, children }: FieldProps) {
    return (
        <div className={className}>
            {label && <Label htmlFor={htmlFor}>{label}</Label>}
            {children}
            {hint && <p className="mt-1.5 text-2xs text-ink-faint">{hint}</p>}
        </div>
    );
}
