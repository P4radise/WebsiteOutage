# WebsiteOutages

Pull Outages from AWS Alerts for Websites down.  Gather the downtime and push into Trackor.
 
## Website Outages 

### SettingsFile
Integration uses SettingsFile to get connection info for Trackor and some AWS configuration.

Example:
```
{
	"trackor.onevizion.com": {
		"url":"trackor.onevizion.com",
		"UserName": "username",
		"Password": "password1"
	},
	"AWSConfig": {
		"Region":"us-east-1",
		"AccessKey": "XXXXXXXXXXXXXXXXx",
		"SecretAccessKey":"YYYYYYYYYYYYYYYYYYYYYYYYYY"
	}
}
```

