# 04 BONUS AUTOMATION IDEAS.MD

# Module 4 Bonus Automation Ideas

Welcome to the fourth module of your journey through our **AI Setup Blueprint** course. In this section titled *04 bonus automation ideas*, we will explore high-value and advanced concepts beyond basic AI setup procedures.

## Advanced Email Management with Python
Automate repetitive email tasks such as filtering, sorting, or sending automated responses using a custom Python script interfacing with your email provider (like Gmail). Let's dive into an example that automates labeling of incoming emails based on their content:

### Prerequisites:
- Familiarity with **Python** and its libraries.
- Basic understanding of web scraping techniques.

```python
import imaplib
import poplib
from email.parser import Parser

def connect_to_email(server, username, password):
    if server.lower() == 'pop3':
        mail = poplib.POP3_SSL('your.pop.mail.server')
    else:
        mail = imaplib.IMAP4_SSL('your.imap.mailserver')

    # Authenticate
    resp = mail.user(username, password)
    
    return mail

def get_emails(mail):
    if server.lower() == 'pop3':
        messages = [b.getmsg alternatively with b.list()[1] or]
        message_list = '\n'.join([e.decode('utf-8') for e in messages])
        parser = Parser()
        emails = []
        
        # Parse the raw email content into Python objects
        parsed_emails = parser.parsestr(message_list)
        return [email.message_from_string(e.as_string()) for e in parsed_emails]
    else:
        resp.select('inbox')
        result, data = mail.search(None, 'ALL')

        ids = re.findall(r'^\d+\z', str(data[0]))
        
        emails = []
        if server.lower() == 'imap':
            return [email.message_from_string(email_data) for email_id in ids]
    
def process_emails(emails):
    labels_to_assign = {
        "urgent": ["IMPORTANT", "URGENT"],
        "newsletter": ["NEWSLETTER"]
    }

    labeled_emails = []
  
    def label_email(email, category_list):
        if any(word.lower() in (email.get_content_type(), email.as_string()).lower()
                for word in category_list): 
            return True
        else:
            return False

    # Process emails and assign labels based on content.
    for i in range(len(emails)):
        labeled = list(map(lambda label, e: (
                   'Label' if label(email)  else None), labels_to_assign.keys(), [emails[i]]))
        
        labeled_emails.append(labeled)
    
def main():
    server = "pop3"
    username = "<your email>"
    password = "<<<<<<< YOUR PASSWORD >>>>>>>"

    mail = connect_to_email(server, username, password)

    emails = get_emails(mail) if not isinstance(email.get(), str):  
        process_emails(email)
    
if __name__ == "__main__":
    main()
```

### Breakdown:
- Connect to the email server using either POP3 or IMAP.
- Fetch all messages from a specific folder (e.g., "inbox").
- Parse through each message and categorize them based on predefined keywords.

**Important:** Replace `your.pop.mail.server` with your actual mail provider's details, along with appropriate credentials for authentication. 

### Note:
Always ensure to handle sensitive information securely by keeping login credentials encrypted or using environment variables instead of hardcoding in scripts directly.


## Real-time Data Processing Using Apache Kafka and Spark

Harness the power of real-time data streams combined with advanced analytics through an integrated solution involving **Apache Kafka** (for handling messaging) alongside **Spark Streaming**.

### Prerequisites:
- Familiarity with Java.
- Basic understanding of distributed systems, stream processing concepts like MapReduce, etc. 

```java
import org.apache.spark.SparkConf;
import org.apache.spark.api.java.JavaRDD;
import org.apache.spark.streaming.StreamingContext;
import org.apache.spark.streaming.kafka010.ConsumerStrategies;
import org.apache.spark.streaming.kafka010.KafkaUtils;
import java.util.Collections;

public class KafkaSparkStreamingExample {
    
    public static void main(String[] args) throws Exception{
        SparkConf conf = new SparkConf().setAppName("Kafka-Spark Example");
        
        StreamingContext ssc = new StreamingContext(conf, Seconds(1));
        
        List<String> topics = Arrays.asList(new String[]{"your-topic"});
        Map<String, Object> kafkaParams = ... // Kafka connection parameters
        
        JavaStreamingContext jssc = null;
        try {
            jssc = StreamUtils
                    .createDirectKafkaStream(this.getClass(), kafkaParams,
                            new SparkSerializer());
        
            ConsumerStrategies<String, String> strategies =
                defaultStrategy(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG);
            
            DStream <String> dstream = KafkaUtils.createDirectStream(
                    jssc,
                    LocationStrategies.PreferConsistent(),
                    topics,
                    sparkDecoder().json(),
                    strategies
            );
        
            JavaRDD rdd = ssc.queueStream(dstream);

            while (rdd.iterator().hasNext()){
                System.out.println(rdd.first());
            }
            
        } finally {
           jssc.close();
       }

    private SparkSerializer <String, String> sparkDecoder(){
        return new org.apache.spark.serializer.SkafkaSparkDeserializer<String,String>(...);
    }



```

### Breakdown:
- Set up a streaming context with **1-second** interval.
- Connect to Kafka using the appropriate connection parameters (not shown for brevity).
- Subscribe to your desired topics and process incoming messages in real-time.

In summary, this module aims at empowering you by showcasing advanced automation techniques that can significantly enhance productivity through email management or real-time data processing capabilities. Apply these concepts with precision following outlined steps while customizing them based on specific project requirements.