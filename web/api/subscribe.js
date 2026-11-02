/**
 * AI Tech Radar Korea — Newsletter Subscription & Instant Report Delivery API
 * Endpoint: POST /api/subscribe
 */

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

module.exports = async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

  if (req.method === "OPTIONS") {
    return res.status(200).end();
  }

  if (req.method === "GET") {
    return res.status(200).json({
      ok: true,
      service: "AI Tech Radar Korea — Subscription API",
      version: "2.0.0",
      status: "operational",
      verifiedBy: "AI Tech Radar Korea 리서치랩"
    });
  }

  if (req.method !== "POST") {
    return res.status(405).json({
      ok: false,
      error: "Method Not Allowed. Please use POST /api/subscribe."
    });
  }

  try {
    let body = req.body || {};
    if (typeof body === "string") {
      try {
        body = JSON.parse(body);
      } catch (_) {
        body = {};
      }
    }

    const rawEmail = typeof body.email === "string" ? body.email.trim().toLowerCase() : "";
    const role = typeof body.role === "string" && body.role.trim() ? body.role.trim() : "1인 창업가/대표";
    const category = typeof body.category === "string" && body.category.trim() ? body.category.trim() : "all";

    if (!rawEmail || !EMAIL_REGEX.test(rawEmail)) {
      return res.status(400).json({
        ok: false,
        error: "유효한 이메일 주소를 입력해 주세요."
      });
    }

    const timestamp = new Date().toISOString();
    const subscriberEvent = {
      event: "NEW_SUBSCRIBER",
      email: rawEmail,
      role,
      category,
      timestamp,
      source: "ai-tech-radar-korea-v2"
    };

    // Structured JSON log for Vercel Runtime Logs persistence
    console.info(JSON.stringify(subscriberEvent));

    // Optional webhook forwarding if SUBSCRIBER_WEBHOOK_URL is configured
    const webhookUrl = process.env.SUBSCRIBER_WEBHOOK_URL;
    let webhookForwarded = false;
    if (webhookUrl && typeof fetch === "function") {
      try {
        const whRes = await fetch(webhookUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(subscriberEvent)
        });
        webhookForwarded = whRes.ok;
      } catch (whErr) {
        console.error(JSON.stringify({
          event: "SUBSCRIBER_WEBHOOK_ERROR",
          email: rawEmail,
          error: whErr && whErr.message ? whErr.message : String(whErr),
          timestamp
        }));
      }
    }

    return res.status(200).json({
      ok: true,
      status: "subscribed",
      message: "구독이 완료되었습니다. 2026 AI & 노코드 12대 툴 실전 과금 비교 마스터 리포트가 즉시 제공됩니다.",
      subscriber: {
        email: rawEmail,
        role,
        category,
        timestamp,
        webhookForwarded
      },
      report: {
        title: "2026 AI & 노코드 12대 툴 실전 과금 비교 마스터 리포트",
        edition: "2026년 11월 최신 공식 가격표 기준",
        issuer: "AI Tech Radar Korea 리서치랩",
        filenameMd: "AI-Tech-Radar-2026-12Tools-Master-Report.md",
        filenameHtml: "AI-Tech-Radar-2026-12Tools-Master-Report-Print.html"
      }
    });
  } catch (err) {
    console.error(JSON.stringify({
      event: "SUBSCRIBE_API_ERROR",
      error: err && err.message ? err.message : String(err),
      timestamp: new Date().toISOString()
    }));
    return res.status(500).json({
      ok: false,
      error: "구독 처리 중 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
    });
  }
};
