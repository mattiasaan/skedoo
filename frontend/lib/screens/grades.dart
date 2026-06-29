// screens/grades.dart
import 'package:flutter/material.dart';
import '../main_layout.dart'; 

class GradesScreen extends StatelessWidget {
  const GradesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B0F0F),
      body: SafeArea(
        child: Column(
          children: [
            _buildAppBar(context),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 8.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildOverallAverageCard(),
                    const SizedBox(height: 28),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Current Subjects',
                          style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
                        ),
                        TextButton(
                          onPressed: () {},
                          child: const Text('View All', style: TextStyle(color: Color(0xFF0E5434), fontWeight: FontWeight.bold)),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    _buildSubjectCardSimple('Advanced Mathematics', 'Last update: Yesterday', '3.9', Icons.functions, Colors.green),
                    const SizedBox(height: 14),
                    _buildOrganicChemistryExpandedCard(),
                    const SizedBox(height: 14),
                    _buildSubjectCardSimple('World Literature', 'Last update: 3 days ago', '3.6', Icons.menu_book_outlined, Colors.green),
                    const SizedBox(height: 14),
                    _buildSubjectCardSimple('Modern History', 'Last update: 1 week ago', '3.8', Icons.public, Colors.teal),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // APP BAR SUPERIORE
  Widget _buildAppBar(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 12.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          IconButton(
            icon: const Icon(Icons.menu, color: Colors.white, size: 32),
            onPressed: () => customScaffoldKey.currentState?.openDrawer(),
          ),
          const Text(
            'Grades',
            style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
          ),
          IconButton(
            icon: const Icon(Icons.notifications_none, color: Colors.white, size: 28), 
            onPressed: () {
              Navigator.pushNamed(context, '/notifications');
            }
          ),
        ],
      ),
    );
  }

  // 1. CARD MEDIA GENERALE CON GRAFICO SFUMATO
  Widget _buildOverallAverageCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF0B1E14), // Sfondo verde scurissimo come da screen
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Overall Average',
                style: TextStyle(color: Colors.white60, fontSize: 15, fontWeight: FontWeight.w500),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFF0E5434).withOpacity(0.4),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.trending_up, color: Color(0xFF10B981), size: 16),
                    SizedBox(width: 4),
                    Text('+0.2', style: TextStyle(color: Color(0xFF10B981), fontWeight: FontWeight.bold, fontSize: 13)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          RichText(
            text: const TextSpan(
              children: [
                TextSpan(text: '3.82', style: TextStyle(color: Color(0xFF10B981), fontSize: 38, fontWeight: FontWeight.bold)),
                TextSpan(text: ' /4.0', style: TextStyle(color: Colors.white38, fontSize: 18, fontWeight: FontWeight.bold)),
              ],
            ),
          ),
          const SizedBox(height: 20),
          // Grafico lineare simulato
          SizedBox(
            width: double.infinity,
            height: 80,
            child: CustomPaint(
              painter: _LineChartPainter(),
            ),
          ),
          const SizedBox(height: 8),
          const Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('SEPT', style: TextStyle(color: Colors.white24, fontSize: 11, fontWeight: FontWeight.bold)),
              Text('NOV', style: TextStyle(color: Colors.white24, fontSize: 11, fontWeight: FontWeight.bold)),
              Text('JAN', style: TextStyle(color: Colors.white24, fontSize: 11, fontWeight: FontWeight.bold)),
              Text('MAR', style: TextStyle(color: Colors.white24, fontSize: 11, fontWeight: FontWeight.bold)),
              Text('NOW', style: TextStyle(color: Colors.white24, fontSize: 11, fontWeight: FontWeight.bold)),
            ],
          ),
        ],
      ),
    );
  }

  // 2. CARD MATERIA SEMPLICE (NON ESPANSA)
  Widget _buildSubjectCardSimple(String title, String subtitle, String grade, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF121818),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.03)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                Text(subtitle, style: const TextStyle(color: Colors.white38, fontSize: 13)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(grade, style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 6),
              Container(
                width: 50,
                height: 3,
                decoration: BoxDecoration(
                  color: const Color(0xFF0E5434),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // 3. CARD ESPANSA DI CHIMICA (Organic Chemistry con Recent Assessments)
  Widget _buildOrganicChemistryExpandedCard() {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF121818),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF0E5434), width: 1.5), // Bordo evidenziato dello screen
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Intestazione Materia
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFF10B981).withOpacity(0.15),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.science_outlined, color: Color(0xFF10B981), size: 24),
              ),
              const SizedBox(width: 16),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Organic Chemistry', style: TextStyle(color: Color(0xFF10B981), fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Text('8 recent grades', style: TextStyle(color: Colors.white38, fontSize: 13)),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  const Text('3.7', style: TextStyle(color: Color(0xFF10B981), fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  Container(
                    width: 50,
                    height: 3,
                    decoration: BoxDecoration(
                      color: const Color(0xFF10B981),
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 20),
          const Text(
            'RECENT ASSESSMENTS',
            style: TextStyle(color: Colors.white38, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 0.8),
          ),
          const Divider(color: Colors.white10, height: 16),
          
          // Lista dei voti recenti interni
          _buildAssessmentItem('Mid-term Exam', 'WRITTEN', 'Mar 12, 2024', '4.0', Colors.blue),
          _buildAssessmentItem('Lab Presentation', 'ORAL', 'Feb 28, 2024', '3.5', Colors.purple),
          _buildAssessmentItem('Titration Practical', 'PRACTICAL', 'Feb 15, 2024', '3.8', Colors.orange),
          
          const SizedBox(height: 12),
          // Bottone "Show All Chemistry Grades"
          SizedBox(
            width: double.infinity,
            child: TextButton(
              onPressed: () {},
              child: const Text(
                'Show All Chemistry Grades',
                style: TextStyle(color: Color(0xFF10B981), fontWeight: FontWeight.bold, fontSize: 14),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // Singola riga del voto interno alla card
  Widget _buildAssessmentItem(String title, String typeTag, String date, String mark, Color tagColor) {
    IconData getIcon() {
      if (typeTag == 'WRITTEN') return Icons.description_outlined;
      if (typeTag == 'ORAL') return Icons.record_voice_over_outlined;
      return Icons.layers_outlined;
    }

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.04),
              shape: BoxShape.circle,
            ),
            child: Icon(getIcon(), color: Colors.white60, size: 18),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: tagColor.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(typeTag, style: TextStyle(color: tagColor, fontSize: 9, fontWeight: FontWeight.bold)),
                    ),
                    const SizedBox(width: 8),
                    Text(date, style: const TextStyle(color: Colors.white38, fontSize: 11)),
                  ],
                ),
              ],
            ),
          ),
          Text(mark, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}

// 4. PAINTER PERSONALIZZATO PER IL GRAFICO AD ANDAMENTO LINEARE SFUMATO
class _LineChartPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paintLine = Paint()
      ..color = const Color(0xFF10B981)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5;

    final path = Path();
    // Punti simulati dell'andamento nello screenshot
    path.moveTo(0, size.height * 0.75);
    path.quadraticBezierTo(size.width * 0.25, size.height * 0.5, size.width * 0.5, size.height * 0.4);
    path.quadraticBezierTo(size.width * 0.75, size.height * 0.3, size.width, size.height * 0.2);

    // Disegna la sfumatura sotto la linea
    final fillPath = Path.from(path);
    fillPath.lineTo(size.width, size.height);
    fillPath.lineTo(0, size.height);
    fillPath.close();

    final paintGradient = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [
          const Color(0xFF10B981).withOpacity(0.2),
          const Color(0xFF10B981).withOpacity(0.0),
        ],
      ).createShader(Rect.fromLTRB(0, 0, size.width, size.height));

    canvas.drawPath(fillPath, paintGradient);
    canvas.drawPath(path, paintLine);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}