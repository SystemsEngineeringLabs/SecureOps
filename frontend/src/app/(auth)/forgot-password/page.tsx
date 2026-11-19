"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Link from "next/link";
import { Button, Input, Card, Alert } from "@/components/ui";

const forgotSchema = z.object({
  email: z.string().min(1, "Email is required").email("Invalid email address"),
});

type ForgotFormData = z.infer<typeof forgotSchema>;

export default function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotFormData>({
    resolver: zodResolver(forgotSchema),
  });

  const onSubmit = async (_data: ForgotFormData) => {
    setIsSubmitting(true);
    // Simulate request — backend endpoint not yet implemented
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsSubmitting(false);
    setSubmitted(true);
  };

  return (
    <Card padding="lg">
      <h2 className="mb-2 text-center text-xl font-semibold">Reset your password</h2>
      <p className="mb-6 text-center text-sm text-gray-500">
        Enter your email and we&apos;ll send you a reset link.
      </p>

      {submitted ? (
        <div className="space-y-4">
          <Alert variant="success">
            If an account with that email exists, a password reset link has been sent.
          </Alert>
          <Link
            href="/login"
            className="btn btn-outline btn-primary w-full"
          >
            Back to sign in
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Email"
            type="email"
            placeholder="you@company.com"
            autoComplete="email"
            error={errors.email?.message}
            {...register("email")}
          />

          <Button type="submit" loading={isSubmitting} className="w-full">
            Send reset link
          </Button>

          <p className="text-center text-sm text-gray-500">
            <Link href="/login" className="text-primary hover:underline">
              Back to sign in
            </Link>
          </p>
        </form>
      )}
    </Card>
  );
}
