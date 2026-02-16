#!/usr/bin/env bash
# =============================================================================
# SloughAI — AWS ECS Fargate 배포 스크립트
# Usage: ./infra/deploy.sh [create|update|delete]
# =============================================================================
set -euo pipefail

STACK_NAME="${STACK_NAME:-slough-ai}"
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
TEMPLATE_FILE="infra/cloudformation.yaml"

# ECR
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${STACK_NAME}"

ACTION="${1:-help}"

case "$ACTION" in
  # ---------------------------------------------------------------------------
  # 1) Docker 이미지 빌드 & ECR 푸시
  # ---------------------------------------------------------------------------
  push)
    echo "🐳 ECR 로그인..."
    aws ecr get-login-password --region "$AWS_REGION" | \
      docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

    IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD)}"
    echo "📦 Docker 이미지 빌드: ${ECR_REPO}:${IMAGE_TAG}"
    docker build -t "${ECR_REPO}:${IMAGE_TAG}" -t "${ECR_REPO}:latest" .

    echo "⬆️  ECR에 푸시..."
    docker push "${ECR_REPO}:${IMAGE_TAG}"
    docker push "${ECR_REPO}:latest"

    echo "✅ 이미지 푸시 완료: ${ECR_REPO}:${IMAGE_TAG}"
    ;;

  # ---------------------------------------------------------------------------
  # 2) CloudFormation 스택 생성
  # ---------------------------------------------------------------------------
  create)
    if [ -z "${DB_PASSWORD:-}" ]; then
      echo "❌ DB_PASSWORD 환경변수를 설정하세요: export DB_PASSWORD=your-password"
      exit 1
    fi
    if [ -z "${SECRET_ARN:-}" ]; then
      echo "❌ SECRET_ARN 환경변수를 설정하세요 (Secrets Manager ARN)"
      exit 1
    fi

    IMAGE_TAG="${IMAGE_TAG:-latest}"
    echo "🚀 CloudFormation 스택 생성: ${STACK_NAME}"
    aws cloudformation create-stack \
      --stack-name "$STACK_NAME" \
      --template-body "file://${TEMPLATE_FILE}" \
      --capabilities CAPABILITY_IAM \
      --region "$AWS_REGION" \
      --parameters \
        ParameterKey=AppImageURI,ParameterValue="${ECR_REPO}:${IMAGE_TAG}" \
        ParameterKey=DBPassword,ParameterValue="${DB_PASSWORD}" \
        ParameterKey=SecretArn,ParameterValue="${SECRET_ARN}" \
        ${CERTIFICATE_ARN:+ParameterKey=CertificateArn,ParameterValue=${CERTIFICATE_ARN}}

    echo "⏳ 스택 생성 대기 중... (약 15-20분 소요)"
    aws cloudformation wait stack-create-complete \
      --stack-name "$STACK_NAME" \
      --region "$AWS_REGION"

    echo "✅ 스택 생성 완료!"
    aws cloudformation describe-stacks \
      --stack-name "$STACK_NAME" \
      --region "$AWS_REGION" \
      --query 'Stacks[0].Outputs' \
      --output table
    ;;

  # ---------------------------------------------------------------------------
  # 3) CloudFormation 스택 업데이트
  # ---------------------------------------------------------------------------
  update)
    IMAGE_TAG="${IMAGE_TAG:-latest}"
    echo "🔄 CloudFormation 스택 업데이트: ${STACK_NAME}"
    aws cloudformation update-stack \
      --stack-name "$STACK_NAME" \
      --template-body "file://${TEMPLATE_FILE}" \
      --capabilities CAPABILITY_IAM \
      --region "$AWS_REGION" \
      --parameters \
        ParameterKey=AppImageURI,ParameterValue="${ECR_REPO}:${IMAGE_TAG}" \
        ParameterKey=DBPassword,UsePreviousValue=true \
        ParameterKey=SecretArn,UsePreviousValue=true \
        ParameterKey=CertificateArn,UsePreviousValue=true

    echo "⏳ 업데이트 대기 중..."
    aws cloudformation wait stack-update-complete \
      --stack-name "$STACK_NAME" \
      --region "$AWS_REGION"

    echo "✅ 스택 업데이트 완료!"
    ;;

  # ---------------------------------------------------------------------------
  # 4) ECS 서비스만 재배포 (이미지 업데이트 후)
  # ---------------------------------------------------------------------------
  deploy)
    CLUSTER="${STACK_NAME}-cluster"
    echo "🔄 ECS 서비스 재배포 (force new deployment)..."
    for svc in "${STACK_NAME}-app-service" "${STACK_NAME}-worker-service" "${STACK_NAME}-beat-service"; do
      echo "  → $svc"
      aws ecs update-service \
        --cluster "$CLUSTER" \
        --service "$svc" \
        --force-new-deployment \
        --region "$AWS_REGION" > /dev/null
    done
    echo "✅ 재배포 트리거 완료 (롤링 업데이트 진행 중)"
    ;;

  # ---------------------------------------------------------------------------
  # 5) 스택 상태 및 출력 확인
  # ---------------------------------------------------------------------------
  status)
    echo "📊 스택 상태:"
    aws cloudformation describe-stacks \
      --stack-name "$STACK_NAME" \
      --region "$AWS_REGION" \
      --query 'Stacks[0].{Status:StackStatus,Created:CreationTime}' \
      --output table

    echo ""
    echo "📋 Outputs:"
    aws cloudformation describe-stacks \
      --stack-name "$STACK_NAME" \
      --region "$AWS_REGION" \
      --query 'Stacks[0].Outputs' \
      --output table
    ;;

  # ---------------------------------------------------------------------------
  # 6) 로그 확인
  # ---------------------------------------------------------------------------
  logs)
    LOG_STREAM="${2:-app}"  # app, worker, beat
    echo "📜 ${LOG_STREAM} 로그 (최근 50줄):"
    aws logs filter-log-events \
      --log-group-name "/ecs/${STACK_NAME}" \
      --log-stream-name-prefix "$LOG_STREAM" \
      --region "$AWS_REGION" \
      --limit 50 \
      --query 'events[].message' \
      --output text
    ;;

  # ---------------------------------------------------------------------------
  # 7) DB 마이그레이션 (ECS Exec으로 실행)
  # ---------------------------------------------------------------------------
  migrate)
    CLUSTER="${STACK_NAME}-cluster"
    TASK_ARN=$(aws ecs list-tasks \
      --cluster "$CLUSTER" \
      --service-name "${STACK_NAME}-app-service" \
      --region "$AWS_REGION" \
      --query 'taskArns[0]' \
      --output text)

    echo "🗄️  DB 마이그레이션 실행 (task: ${TASK_ARN})..."
    aws ecs execute-command \
      --cluster "$CLUSTER" \
      --task "$TASK_ARN" \
      --container app \
      --interactive \
      --command "alembic upgrade head" \
      --region "$AWS_REGION"
    ;;

  # ---------------------------------------------------------------------------
  # 8) 스택 삭제
  # ---------------------------------------------------------------------------
  delete)
    echo "⚠️  스택 삭제: ${STACK_NAME} (복구 불가!)"
    read -p "정말 삭제하시겠습니까? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
      aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"
      echo "🗑️  스택 삭제 시작. 완료까지 수 분 소요됩니다."
    else
      echo "취소됨."
    fi
    ;;

  # ---------------------------------------------------------------------------
  # Help
  # ---------------------------------------------------------------------------
  *)
    echo "SloughAI AWS 배포 스크립트"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  push      Docker 이미지 빌드 & ECR 푸시"
    echo "  create    CloudFormation 스택 생성 (최초 1회)"
    echo "  update    CloudFormation 스택 업데이트"
    echo "  deploy    ECS 서비스 재배포 (이미지 변경 후)"
    echo "  status    스택 상태 확인"
    echo "  logs      ECS 로그 확인 (logs [app|worker|beat])"
    echo "  migrate   Alembic DB 마이그레이션 실행"
    echo "  delete    스택 삭제"
    echo ""
    echo "환경변수:"
    echo "  DB_PASSWORD     RDS 패스워드 (create 시 필수)"
    echo "  SECRET_ARN      Secrets Manager ARN (create 시 필수)"
    echo "  CERTIFICATE_ARN ACM 인증서 ARN (HTTPS, 선택)"
    echo "  IMAGE_TAG       Docker 이미지 태그 (기본: latest)"
    echo "  AWS_REGION      AWS 리전 (기본: ap-northeast-2)"
    ;;
esac
