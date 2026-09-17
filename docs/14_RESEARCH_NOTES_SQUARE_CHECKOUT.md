# Research Notes — Square Hosted Checkout Pattern

## Finding

LNbits' current Square fiat provider uses Square's hosted online-checkout payment-link endpoint rather than a hidden or special Bitcoin API.

Its pattern is:

```text
create Square order/payment link
        ↓
redirect customer to square.link
        ↓
Square processes payment
        ↓
Square payment webhook
        ↓
retrieve/reconcile Square order/payment
        ↓
require COMPLETED
```

This is a useful pattern for BMB.

## What we adopt

- hosted Square checkout
- Square order IDs
- idempotent creation
- metadata/reference linking
- webhook signature verification
- webhook-driven payment completion
- API reconciliation after webhook or timeout

## What we do not adopt

LNbits' Square fiat-provider behavior credits an internal LNbits wallet with a satoshi-equivalent ledger balance after fiat payment.

That behavior is appropriate for LNbits wallet funding but unnecessary for BMB ecommerce.

BMB therefore calls Square directly.

## Lightning

LNbits does not solve the required BMB Lightning settlement problem.

The project requires:

```text
Lightning -> Square -> automatic USD -> normal Printful flow
```

So Lightning remains deferred until Square exposes the necessary official API.
