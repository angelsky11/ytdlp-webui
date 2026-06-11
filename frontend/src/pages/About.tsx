import { Card, Typography, Space, Tag, Divider } from 'antd';
import { GithubOutlined, SendOutlined } from '@ant-design/icons';
import { useLocale } from '../i18n';

const { Title, Text, Paragraph, Link } = Typography;

declare const __APP_VERSION__: string;

export default function About() {
  const { t, resolve } = useLocale();
  const features = resolve('about.featuresList') as string[] | undefined;
  const tech = resolve('about.techList') as string[] | undefined;

  return (
    <Card>
      <Title level={4}>{t('about.title')}</Title>
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <Paragraph>
          <Text strong>yt-dlp Web UI</Text> {t('about.description')}
        </Paragraph>

        <Divider style={{ margin: '8px 0' }} />

        <Paragraph>
          <Text strong>{t('about.features')}:</Text>
          <ul>
            {(Array.isArray(features) ? features : []).map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </Paragraph>

        <Paragraph>
          <Text strong>{t('about.techStack')}:</Text>
          <ul>
            {(Array.isArray(tech) ? tech : []).map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </Paragraph>

        <Divider style={{ margin: '8px 0' }} />

        <Paragraph>
          <Space size="middle" wrap>
            <Link href={t('about.githubLink')} target="_blank">
              <GithubOutlined /> {t('about.github')}
            </Link>
            <Link href={t('about.telegramLink')} target="_blank">
              <SendOutlined /> {t('about.telegram')}
            </Link>
          </Space>
        </Paragraph>

        <Paragraph>
          <Tag color="blue">{t('about.version', { version: __APP_VERSION__ })}</Tag>
        </Paragraph>
      </Space>
    </Card>
  );
}
