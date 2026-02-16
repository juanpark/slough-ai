#!/usr/bin/env bash
# =============================================================================
# SloughAI — IAM 정책 생성 및 그룹에 연결
# Usage: ./infra/iam/setup-iam.sh
#
# ⚠️  Admin 권한이 있는 계정으로 실행하세요!
#     이미 생성된 그룹(slough-ai)에 정책을 연결합니다.
# =============================================================================
set -euo pipefail

IAM_GROUP="slough-ai"
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
POLICY_DIR="$(cd "$(dirname "$0")" && pwd)"

POLICIES=(
  "slough-ai-cfn-deploy:01-cfn-deploy.json"
  "slough-ai-vpc-network:02-vpc-network.json"
  "slough-ai-ecs-fargate:03-ecs-fargate.json"
  "slough-ai-data-stores:04-data-stores.json"
  "slough-ai-alb-waf:05-alb-waf.json"
  "slough-ai-supporting:06-supporting.json"
)

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "🔑 AWS Account: ${AWS_ACCOUNT_ID}"
echo "👥 대상 그룹: ${IAM_GROUP}"
echo ""

# ─── 1. 정책 생성 및 그룹에 연결 ──────────────────────────────────────
for entry in "${POLICIES[@]}"; do
  POLICY_NAME="${entry%%:*}"
  POLICY_FILE="${entry##*:}"
  POLICY_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${POLICY_NAME}"

  echo "📋 정책: ${POLICY_NAME}"

  # 정책이 이미 존재하는지 확인
  if aws iam get-policy --policy-arn "$POLICY_ARN" &>/dev/null; then
    echo "   🔄 기존 정책 버전 업데이트..."
    OLD_VERSIONS=$(aws iam list-policy-versions \
      --policy-arn "$POLICY_ARN" \
      --query 'Versions[?!IsDefaultVersion].VersionId' \
      --output text)
    for ver in $OLD_VERSIONS; do
      aws iam delete-policy-version --policy-arn "$POLICY_ARN" --version-id "$ver" 2>/dev/null || true
    done
    aws iam create-policy-version \
      --policy-arn "$POLICY_ARN" \
      --policy-document "file://${POLICY_DIR}/${POLICY_FILE}" \
      --set-as-default > /dev/null
  else
    echo "   🆕 새 정책 생성..."
    aws iam create-policy \
      --policy-name "$POLICY_NAME" \
      --policy-document "file://${POLICY_DIR}/${POLICY_FILE}" \
      --description "SloughAI deploy policy - ${POLICY_NAME}" > /dev/null
  fi

  # 그룹에 연결
  aws iam attach-group-policy \
    --group-name "$IAM_GROUP" \
    --policy-arn "$POLICY_ARN"
  echo "   ✅ ${IAM_GROUP} 그룹에 연결 완료"
done

echo ""
echo "============================================="
echo "✅ IAM 정책 설정 완료!"
echo ""
echo "${IAM_GROUP} 그룹에 할당된 정책 (6개):"
for entry in "${POLICIES[@]}"; do
  POLICY_NAME="${entry%%:*}"
  echo "  • ${POLICY_NAME}"
done
echo ""
echo "그룹 내 모든 사용자가 배포 권한을 갖습니다."
echo ""
echo "다음 단계:"
echo "  ./infra/deploy.sh create"
echo "============================================="
