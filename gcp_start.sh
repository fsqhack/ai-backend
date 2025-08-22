export GCP_PROJECT_ID="sample-project-1-464117"
export SERVICE_AC_DISPLAYNAME="sample-project-1-464117"
export LOCATION="us-central1"
export GAR_REPOSITORY_ID="fsq-ai-repo"
export GAR_LOCATION="us-central1"


gcloud config set project $GCP_PROJECT_ID

# gcloud iam service-accounts create $SERVICE_AC_DISPLAYNAME --display-name $SERVICE_AC_DISPLAYNAME

# gcloud services enable cloudresourcemanager.googleapis.com \
#     artifactregistry.googleapis.com \
#     iam.googleapis.com \
#     storage.googleapis.com \
#     aiplatform.googleapis.com \
#     run.googleapis.com \
#     --project=$GCP_PROJECT_ID


# for role in resourcemanager.projectIamAdmin \
#             iam.serviceAccountUser \
#             run.admin \
#             artifactregistry.writer \
#             artifactregistry.reader \
#             artifactregistry.admin \
#             storage.admin \
#             storage.objectAdmin \
#             storage.objectViewer \
#             storage.objectCreator \
#             aiplatform.user \
#             aiplatform.admin; do
#     gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
#         --member=serviceAccount:$SERVICE_AC_DISPLAYNAME@$GCP_PROJECT_ID.iam.gserviceaccount.com \
#         --role=roles/$role
# done



# gcloud iam service-accounts keys create key.json \
#     --iam-account=$SERVICE_AC_DISPLAYNAME@$GCP_PROJECT_ID.iam.gserviceaccount.com



gcloud artifacts repositories create $GAR_REPOSITORY_ID \
    --project=$GCP_PROJECT_ID \
    --location=$GAR_LOCATION \
    --repository-format=docker \
    --description="Docker repository for Python server"