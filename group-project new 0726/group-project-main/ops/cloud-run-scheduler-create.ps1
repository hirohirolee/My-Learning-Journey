$ProjectId = "group-project-503201"
$Region = "asia-east1"
$JobName = "daily-dashboard-sync-new"
$ServiceUrl = "https://group-project-v1-320496839513.asia-east1.run.app"
$Schedule = "0 3 * * *"
$TimeZone = "Asia/Taipei"
$SyncUrl = "$ServiceUrl/api/ml-dashboard/sync?dry_run=false&force=false"

gcloud config set project $ProjectId
gcloud services enable cloudscheduler.googleapis.com

gcloud scheduler jobs create http $JobName `
  --location $Region `
  --schedule $Schedule `
  --time-zone $TimeZone `
  --uri $SyncUrl `
  --http-method POST
