import { Card, Typography, Space } from 'antd';
import { GithubOutlined, SendOutlined } from '@ant-design/icons';
import { useLocale } from '../i18n';

const { Title, Text, Paragraph, Link } = Typography;

export default function About() {
  const { t } = useLocale();
  const features = t('about.featuresList');
  const tech = t('about.techList');

  return (
    <Card>
      <Title level={4}>{t('about.title')}</Title>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Paragraph>
          <Text strong>yt-dlp Web UI</Text> {t('about.description')}
        </Paragraph>

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
            {(Array.isArray(tech) ? tech : []).map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </Paragraph>

        <Paragraph>
          <Space size="middle">
            <Link href={t('about.githubLink')} target="_blank">
              <GithubOutlined /> {t('about.github')}
            </Link>
            <Link href={t('about.telegramLink')} target="_blank">
              <SendOutlined /> {t('about.telegram')}
            </Link>
          </Space>
        </Paragraph>

        <Paragraph>
          <Text type="secondary">{t('about.version', { version: t('about.versionNumber') })}</Text>
        </Paragraph>
      </Space>
    </Card>
  );
}
