import React, { useCallback, useEffect, useRef } from "react";
import { cn } from "./cn";
import { controlClasses } from "./control";

export interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
    /** Grow the textarea to fit its content (disables manual resize). */
    autoGrow?: boolean;
}

/**
 * A comfortable, reusable multi-line text editor: generous min-height, relaxed
 * line-height, and user-resizable by default. Pass `autoGrow` to have it expand
 * to fit its content instead.
 */
export const TextArea = React.forwardRef<HTMLTextAreaElement, TextAreaProps>(function TextArea(
    { className, autoGrow = false, onInput, value, ...rest },
    ref
) {
    const innerRef = useRef<HTMLTextAreaElement | null>(null);

    const setRefs = useCallback(
        (node: HTMLTextAreaElement | null) => {
            innerRef.current = node;
            if (typeof ref === "function") ref(node);
            else if (ref) ref.current = node;
        },
        [ref]
    );

    const resize = useCallback(() => {
        const el = innerRef.current;
        if (!el) return;
        el.style.height = "auto";
        el.style.height = `${el.scrollHeight}px`;
    }, []);

    // Re-fit on programmatic value changes (e.g. loading a template).
    useEffect(() => {
        if (autoGrow) resize();
    }, [autoGrow, value, resize]);

    return (
        <textarea
            ref={setRefs}
            value={value}
            onInput={(e) => {
                if (autoGrow) resize();
                onInput?.(e);
            }}
            className={cn(
                controlClasses,
                "min-h-[8rem] leading-relaxed",
                autoGrow ? "resize-none overflow-hidden" : "resize-y",
                className
            )}
            {...rest}
        />
    );
});
