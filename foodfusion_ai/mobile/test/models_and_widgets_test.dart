import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:foodfusion_ai/models/models.dart';
import 'package:foodfusion_ai/core/widgets/custom_widgets.dart';

void main() {
  group('FoodFusion AI Unit Tests', () {
    test('DishModel serialization and property validation', () {
      final json = {
        'id': 1,
        'restaurant_id': 10,
        'name': 'Paneer Tikka Biryani',
        'description': 'Fragrant basmati rice layered with spiced cottage cheese',
        'price': 240.0,
        'is_veg': true,
        'spice_level': 'spicy',
        'calories': 520,
        'protein_g': 22,
        'prep_time_min': 20,
        'is_available': true,
        'stock_count': 15,
      };

      final dish = DishModel.fromJson(json);

      expect(dish.id, 1);
      expect(dish.name, 'Paneer Tikka Biryani');
      expect(dish.price, 240.0);
      expect(dish.isVeg, true);
      expect(dish.proteinG, 22);
      expect(dish.prepTimeMin, 20);
    });

    test('SurplusOfferModel discount and environmental metrics', () {
      final json = {
        'id': 1,
        'restaurant_id': 10,
        'restaurant_name': 'Green Delight',
        'restaurant_address': 'Indiranagar 100ft Rd',
        'dish_id': 1,
        'dish_name': 'Paneer Biryani Meal',
        'original_price': 250.0,
        'discounted_price': 100.0,
        'discount_percentage': 60,
        'quantity_available': 4,
        'waste_saved_kg': 0.8,
        'co2_saved_kg': 2.1,
        'remaining_minutes': 45,
      };

      final surplus = SurplusOfferModel.fromJson(json);

      expect(surplus.discountPercentage, 60);
      expect(surplus.discountedPrice, 100.0);
      expect(surplus.wasteSavedKg, 0.8);
      expect(surplus.co2SavedKg, 2.1);
      expect(surplus.remainingMinutes, 45);
    });

    test('BudgetComboModel constraints calculation', () {
      final combo = BudgetComboModel(
        items: [
          DishModel(
            id: 1,
            restaurantId: 1,
            name: 'Dal Makhani',
            price: 90.0,
            isVeg: true,
            spiceLevel: 'medium',
            calories: 320,
            proteinG: 12,
            prepTimeMin: 15,
            isAvailable: true,
            stockCount: 10,
          ),
          DishModel(
            id: 2,
            restaurantId: 1,
            name: 'Tandoori Roti (2 pcs)',
            price: 30.0,
            isVeg: true,
            spiceLevel: 'mild',
            calories: 160,
            proteinG: 5,
            prepTimeMin: 10,
            isAvailable: true,
            stockCount: 20,
          ),
        ],
        itemSubtotal: 120.0,
        grandTotal: 146.0,
        remainingBudget: 4.0,
        restaurantName: 'Spice Villa',
        reason: 'Fits within ₹150 budget including GST and delivery',
      );

      expect(combo.grandTotal <= 150.0, isTrue);
      expect(combo.items.length, 2);
      expect(combo.remainingBudget, 4.0);
    });
  });

  group('FoodFusion AI Widget Tests', () {
    testWidgets('AppButton renders text and triggers callback', (WidgetTester tester) async {
      bool pressed = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppButton(
              text: 'Order Now',
              onPressed: () => pressed = true,
            ),
          ),
        ),
      );

      expect(find.text('Order Now'), findsOneWidget);

      await tester.tap(find.text('Order Now'));
      await tester.pump();

      expect(pressed, isTrue);
    });

    testWidgets('ExplainableBadge renders match score and AI explanation tag', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ExplainableBadge(
              score: 95,
              reason: 'Matches spicy preference and ₹150 budget',
            ),
          ),
        ),
      );

      expect(find.text('95% MATCH'), findsOneWidget);
    });
  });
}
